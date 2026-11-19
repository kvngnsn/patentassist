#!/usr/bin/env python3
"""Verify every reference in prior-art.json against fetched records.

For each reference: normalize the number, fetch it (cache-first), compare title (fuzzy token
ratio >= 0.85), dates, and assignee/authors; set verified / verified_how / verified_on; fill
missing metadata from the record; merge a publication and its grant into one reference
(`family`); compute prior_art_basis against cutoff_date.

Examples:
    python3 scripts/verify_refs.py                 # verify patent/prior-art.json, write results back
    python3 scripts/verify_refs.py --offline       # cache only
    python3 scripts/verify_refs.py --dry-run --json

prior_art_basis:
    102(a)(1)       published (or patented, or otherwise public) before cutoff_date
    102(a)(2)       US patent, published US application, or WO (designating the US) whose effective
                    filing date is before cutoff_date but which published on/after it
    not_prior_art   neither
    needs_evidence  web/product reference without a provable date, or a date too coarse to compare

Findings: BLOCK on number/kind/title/date/assignee mismatch or a number that does not exist;
WARN when a reference cannot be fetched (it is left verified: false).
Exit codes: 0 no blocking findings, 1 blocking findings, 2 bad input, 3 (not used: fetch
failures are WARN so the rest of the file still gets verified).
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from normalize_number import kindless, normalize  # noqa: E402
from npl_fetch import cmd_arxiv, cmd_doi, cmd_wayback, token_ratio  # noqa: E402
from patent_fetch import fetch_one  # noqa: E402
from state import (UsageError, add_common, audit, cli_main, finalize, finding, load_prior_art,  # noqa: E402
                   new_result, save_prior_art, to_namespace, today_iso)

TITLE_MIN = 0.85
NAME_MIN = 0.80

_CORP = r"\b(?:co|company|corp|corporation|inc|incorporated|ltd|limited|llc|l\.l\.c|plc|gmbh|ag|bv|b\.v|nv|sa|" \
        r"sas|srl|spa|kk|k\.k|oy|ab|as|lp|llp|pty|pte|the|of|and)\b"


def norm_name(s):
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[.,;:()'\"]", " ", s)
    s = re.sub(_CORP, " ", s)
    return re.sub(r"\s+", " ", s).strip()


def name_match(given, candidates):
    """True if `given` (one string, possibly 'A; B' or 'Smith et al.') matches any candidate name."""
    g_all = [x for x in re.split(r";|\band\b|\bet al\b\.?|,(?=\s*[A-Z][a-z]+\s+[A-Z])", given or "") if x.strip()]
    if not g_all:
        g_all = [given or ""]
    cands = [norm_name(c) for c in candidates if c]
    for g in g_all:
        gn = norm_name(g)
        if not gn:
            continue
        gt = set(gn.split())
        for c in cands:
            if not c:
                continue
            ct = set(c.split())
            if gn == c or (gt and gt <= ct) or (ct and ct <= gt):
                return True
            if token_ratio(gn, c) >= NAME_MIN:
                return True
            # surname-only match ("Alataas" vs "Reem Jafar ALATAAS")
            if len(gt) == 1 and gt & ct:
                return True
    return False


def _cmp_date(given, actual):
    """Compare dates at the precision given (YYYY, YYYY-MM, YYYY-MM-DD)."""
    if not given or not actual:
        return None
    g, a = str(given)[:10], str(actual)[:10]
    n = min(len(g), len(a))
    return g[:n] == a[:n]


def _date_lt(a, cutoff):
    """a < cutoff with partial dates; returns True/False or None when too coarse to tell."""
    a = str(a)
    c = str(cutoff)[:10]
    if len(a) >= 10:
        return a[:10] < c
    if len(a) == 7:
        if a < c[:7]:
            return True
        if a > c[:7]:
            return False
        return None
    if len(a) == 4:
        if a < c[:4]:
            return True
        if a > c[:4]:
            return False
        return None
    return None


def family_pub_dates(rec):
    """{number: date} for publications of the same application seen in the record's events."""
    out = {}
    if rec.get("number") and rec.get("publication_date"):
        out[rec["number"]] = rec["publication_date"]
    for e in rec.get("events") or []:
        if e.get("type") == "publication" and e.get("document") and e.get("date"):
            out[e["document"]] = e["date"]
    return out


def earliest(*ds):
    ds = [d for d in ds if d]
    return min(ds) if ds else None


def is_us_patent_doc(number, doc_type):
    return (number or "").startswith("US") and doc_type in ("patent", "application_pub", "design", "plant", "reissue")


def compute_basis(ref, cutoff):
    """Return (basis, note)."""
    rtype = ref.get("type")
    pub = earliest(ref.get("pub_date"), ref.get("grant_date"))
    number = ref.get("number") or ""
    if rtype in ("web", "product") and not pub:
        return "needs_evidence", "no provable public date"
    if not pub and rtype == "npl":
        return "needs_evidence", "no publication date"
    if pub:
        lt = _date_lt(pub, cutoff)
        if lt is True:
            return "102(a)(1)", "public %s, before cutoff %s" % (pub, cutoff)
        if lt is None:
            return "needs_evidence", "date %s is too coarse to compare with cutoff %s" % (pub, cutoff)
    eff = earliest(ref.get("priority_date"), ref.get("filing_date"))
    norm = normalize(number) if number else {"ok": False}
    doc_type = norm.get("doc_type") if norm.get("ok") else None
    if eff and _date_lt(eff, cutoff):
        if is_us_patent_doc(number, doc_type):
            return "102(a)(2)", "US document effectively filed %s, published %s (on/after cutoff %s)" % (eff, pub, cutoff)
        if number.startswith("WO"):
            return "102(a)(2)", ("WO publication effectively filed %s, published %s; counts under 102(a)(2) "
                                 "because it designates the US (all PCT filings since 2004 do)" % (eff, pub))
    if not pub:
        return "needs_evidence", "no publication date"
    return "not_prior_art", "published %s, not before cutoff %s%s" % (
        pub, cutoff, "" if not eff else "; effectively filed %s" % eff)


def _assignee_text(rec):
    a = [x for x in (rec.get("assignees") or []) if x and x.lower() != "individual"]
    if a:
        return "; ".join(a)
    return "; ".join(rec.get("inventors") or []) or None


# --------------------------------------------------------------------------- per reference


def verify_patent_ref(ref, a, res):
    where = ref.get("id") or ref.get("number") or "?"
    number = ref.get("number")
    norm = normalize(number)
    if not norm.get("ok"):
        res["findings"].append(finding("BLOCK", "bad_number", where, "cannot parse number %r" % number))
        ref["verified"] = False
        return None
    if norm["doc_type"] == "application_no":
        res["findings"].append(finding("BLOCK", "application_number", where,
                                       "%s is an application number; cite its publication or patent" % number))
        ref["verified"] = False
        return None
    r = fetch_one(number, a.dir, offline=a.offline, no_audit=a.no_audit)
    rec = r.get("record")
    if r["status"] == "not_found":
        res["findings"].append(finding("BLOCK", "not_found", where,
                                       "%s does not exist on Google Patents (tried %s)" % (number, ", ".join(r["tried"]))))
        ref["verified"] = False
        audit(a.dir, "verify", a.no_audit, ref=where, result="not_found", number=number)
        return None
    if not rec:
        res["findings"].append(finding("WARN", "unverified", where, "could not fetch %s: %s; left verified: false"
                                       % (number, r.get("message") or r["status"])))
        ref["verified"] = False
        audit(a.dir, "verify", a.no_audit, ref=where, result="unverified", number=number, reason=r["status"])
        return None

    blocks_before = len([f for f in res["findings"] if f["level"] == "BLOCK"])
    matched, filled = ["number"], []
    actual = rec.get("number") or norm["canonical"]
    if norm.get("kind") and rec.get("kind") and norm["kind"] != rec["kind"]:
        res["findings"].append(finding("BLOCK", "kind_mismatch", where,
                                       "reference says %s but the document is %s" % (norm["canonical"], actual)))
    elif kindless(actual) != kindless(norm["canonical"]):
        res["findings"].append(finding("BLOCK", "number_mismatch", where,
                                       "requested %s, source returned %s" % (norm["canonical"], actual)))
    else:
        if norm.get("kind"):
            matched.append("kind")
        else:
            filled.append("kind")
        if ref.get("number") != actual:
            ref["number"] = actual

    # title
    if ref.get("title"):
        score = token_ratio(ref["title"], rec.get("title"))
        if score >= TITLE_MIN:
            matched.append("title")
        else:
            res["findings"].append(finding("BLOCK", "title_mismatch", where,
                                           "title %r vs source %r (similarity %.2f < %.2f)"
                                           % (ref["title"], rec.get("title"), score, TITLE_MIN)))
    elif rec.get("title"):
        ref["title"] = rec["title"]
        filled.append("title")

    # dates
    pubs = family_pub_dates(rec)
    date_fields = (("priority_date", rec.get("priority_date")), ("filing_date", rec.get("filing_date")),
                   ("grant_date", rec.get("grant_date")))
    date_ok = True
    for field, actual_d in date_fields:
        if ref.get(field):
            c = _cmp_date(ref[field], actual_d)
            if c is False:
                date_ok = False
                res["findings"].append(finding("BLOCK", "date_mismatch", where,
                                               "%s %s vs source %s" % (field, ref[field], actual_d)))
        elif actual_d:
            ref[field] = actual_d
            filled.append(field)
    earliest_pub = earliest(*pubs.values()) or rec.get("publication_date")
    if ref.get("pub_date"):
        if not any(_cmp_date(ref["pub_date"], d) for d in list(pubs.values()) + [rec.get("publication_date")] if d):
            date_ok = False
            res["findings"].append(finding("BLOCK", "date_mismatch", where,
                                           "pub_date %s matches no publication of this application (%s)"
                                           % (ref["pub_date"], ", ".join("%s %s" % kv for kv in sorted(pubs.items())))))
    elif earliest_pub:
        ref["pub_date"] = earliest_pub
        filled.append("pub_date")
    if date_ok and (any(ref.get(f) for f, _ in date_fields) or ref.get("pub_date")):
        matched.append("dates")

    # assignee / applicant
    names = list(rec.get("assignees") or []) + list(rec.get("assignees_current") or []) + list(rec.get("inventors") or [])
    if ref.get("assignee_or_authors"):
        if name_match(ref["assignee_or_authors"], names):
            matched.append("assignee")
        else:
            res["findings"].append(finding("BLOCK", "assignee_mismatch", where,
                                           "assignee %r not found among %s" % (ref["assignee_or_authors"], names)))
    else:
        txt = _assignee_text(rec)
        if txt:
            ref["assignee_or_authors"] = txt
            filled.append("assignee_or_authors")

    # other fill-ins
    for k_ref, val in (("country", rec.get("country")), ("kind", rec.get("kind")), ("url", rec.get("url"))):
        if not ref.get(k_ref) and val:
            ref[k_ref] = val
    if not ref.get("type"):
        ref["type"] = "application" if rec.get("doc_type") == "application_pub" else "patent"
    ref["_app_no"] = rec.get("application_number")
    ref["_family_pubs"] = sorted(pubs)
    if any("machine translation" in str(n).lower() for n in rec.get("notes") or []):
        ref["machine_translation"] = True  # chart.py tags these cells [machine translation – review]
    else:
        ref.pop("machine_translation", None)

    # experimental ODP cross-check
    odp = (rec.get("enrichment") or {}).get("uspto_odp") or {}
    if odp.get("ok") and odp.get("fields", {}).get("title"):
        if token_ratio(odp["fields"]["title"], rec.get("title")) < TITLE_MIN:
            res["findings"].append(finding("WARN", "odp_title_differs", where,
                                           "ODP title %r differs from Google %r" % (odp["fields"]["title"], rec.get("title"))))
        else:
            matched.append("odp_title")

    new_blocks = len([f for f in res["findings"] if f["level"] == "BLOCK"]) - blocks_before
    src = "google_patents" + ("+uspto_odp" if "odp_title" in matched else "")
    if new_blocks == 0:
        ref["verified"] = True
        how = "%s: %s" % (src, "+".join(matched))
        if filled:
            how += "; filled %s" % ", ".join(filled)
        if src == "google_patents":
            how += " (single source: Google Patents)"
        ref["verified_how"] = how
        ref["verified_on"] = today_iso(a.today)
    else:
        ref["verified"] = False
        ref["verified_how"] = "mismatch against %s" % src
        ref["verified_on"] = today_iso(a.today)
    audit(a.dir, "verify", a.no_audit, ref=where, number=ref.get("number"),
          result="verified" if ref["verified"] else "mismatch", how=ref.get("verified_how"))
    return rec


def verify_npl_ref(ref, a, res):
    where = ref.get("id") or "?"
    rtype = ref.get("type")
    sub = new_result()
    import argparse as _ap
    ns = _ap.Namespace(dir=a.dir, offline=a.offline, no_audit=a.no_audit, force=False, target=None)
    try:
        if ref.get("doi"):
            ns.target = ref["doi"]
            cmd_doi(ns, sub)
        elif ref.get("arxiv_id") or re.match(r"^(arxiv:)?\d{4}\.\d{4,5}(v\d+)?$", str(ref.get("number") or ""), re.I):
            ns.target = ref.get("arxiv_id") or ref["number"]
            cmd_arxiv(ns, sub)
        elif ref.get("url"):
            ns.target = ref["url"]
            cmd_wayback(ns, sub)
        else:
            res["findings"].append(finding("WARN", "unverified", where,
                                           "%s reference has no DOI, arXiv id, or URL to check; left verified: false" % rtype))
            ref["verified"] = False
            return None
    except Exception as e:  # network or bad identifier: keep going
        res["findings"].append(finding("WARN", "unverified", where, "could not fetch: %s" % e))
        ref["verified"] = False
        return None
    rec = sub.get("record")
    if not rec:
        lvl = "BLOCK" if any(f["code"] == "not_found" for f in sub["findings"]) else "WARN"
        res["findings"].append(finding(lvl, "not_found" if lvl == "BLOCK" else "unverified", where,
                                       "; ".join(f["message"] for f in sub["findings"]) or "no record"))
        ref["verified"] = False
        return None
    blocks_before = len([f for f in res["findings"] if f["level"] == "BLOCK"])
    matched, filled = [], []
    if rec.get("doc_type") == "web":
        cap = rec.get("earliest_capture")
        if not cap:
            res["findings"].append(finding("WARN", "no_capture", where, "no Wayback capture; date unproven"))
            ref["verified"] = False
            ref["prior_art_basis_note"] = "needs evidence of the public date"
            return rec
        matched.append("wayback capture %s" % cap["date"])
        if ref.get("pub_date") and ref["pub_date"] < cap["date"]:
            res["findings"].append(finding("WARN", "date_unproven", where,
                                           "pub_date %s is earlier than the earliest capture %s; the earlier date needs "
                                           "its own evidence" % (ref["pub_date"], cap["date"])))
            ref["pub_date_claimed"] = ref["pub_date"]
            ref["pub_date"] = cap["date"]
        elif not ref.get("pub_date"):
            ref["pub_date"] = cap["date"]
            filled.append("pub_date")
        ref["evidence_url"] = cap["capture_url"]
    else:
        if ref.get("title"):
            s = token_ratio(ref["title"], rec.get("title"))
            if s >= TITLE_MIN:
                matched.append("title")
            else:
                res["findings"].append(finding("BLOCK", "title_mismatch", where, "title %r vs source %r (%.2f)"
                                               % (ref["title"], rec.get("title"), s)))
        elif rec.get("title"):
            ref["title"] = rec["title"]
            filled.append("title")
        if ref.get("pub_date"):
            if _cmp_date(ref["pub_date"], rec.get("pub_date")) is False:
                res["findings"].append(finding("BLOCK", "date_mismatch", where, "pub_date %s vs source %s"
                                               % (ref["pub_date"], rec.get("pub_date"))))
            else:
                matched.append("date")
        elif rec.get("pub_date"):
            ref["pub_date"] = rec["pub_date"]
            filled.append("pub_date")
        if ref.get("assignee_or_authors"):
            if name_match(ref["assignee_or_authors"], rec.get("authors") or []):
                matched.append("authors")
            else:
                res["findings"].append(finding("BLOCK", "author_mismatch", where, "authors %r not in %s"
                                               % (ref["assignee_or_authors"], (rec.get("authors") or [])[:6])))
        elif rec.get("authors"):
            ref["assignee_or_authors"] = "; ".join(rec["authors"])
            filled.append("assignee_or_authors")
        if not ref.get("url") and rec.get("url"):
            ref["url"] = rec["url"]
        if not ref.get("doi") and rec.get("doi"):
            ref["doi"] = rec["doi"]
        if not ref.get("venue") and rec.get("venue"):
            ref["venue"] = rec["venue"]
    ref["cache"] = rec.get("number")
    new_blocks = len([f for f in res["findings"] if f["level"] == "BLOCK"]) - blocks_before
    ref["verified"] = new_blocks == 0
    how = "%s: %s" % (rec.get("source"), "+".join(matched) or "identifier resolved")
    if filled:
        how += "; filled %s" % ", ".join(filled)
    ref["verified_how"] = how if ref["verified"] else "mismatch against %s" % rec.get("source")
    ref["verified_on"] = today_iso(a.today)
    audit(a.dir, "verify", a.no_audit, ref=where, result="verified" if ref["verified"] else "mismatch",
          how=ref["verified_how"])
    return rec


# --------------------------------------------------------------------------- family merge


def _app_key(app):
    return re.sub(r"[^A-Z0-9]", "", (app or "").upper()) or None


def merge_families(refs, pa, res):
    """Merge references that are publications of one application (pub + grant), and exact duplicates."""
    groups = {}
    order = []
    for r in refs:
        key = None
        if r.get("type") in ("patent", "application") and r.get("number"):
            key = ("app", _app_key(r.get("_app_no"))) if r.get("_app_no") else ("num", r["number"])
        else:
            key = ("id", r.get("id") or id(r))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)
    # also link refs whose number appears in another's same-application publication list
    out = []
    renames = {}
    for key in order:
        members = groups[key]
        if len(members) == 1:
            out.append(members[0])
            continue
        grants = [m for m in members if normalize(m["number"]).get("doc_type") in ("patent", "reissue", "design", "plant")]
        primary_doc = grants[0] if grants else members[0]
        keep = members[0]  # keep the first reference's id
        others = [m for m in members if m is not keep]
        fam = list(keep.get("family") or [])
        for m in members:
            for n in [m.get("number")] + list(m.get("family") or []):
                if n and n != primary_doc["number"] and n not in fam:
                    fam.append(n)
        merged_ids = [m.get("id") for m in others]
        # element map: keep keep's entries; add others' where keep lacks or is weaker
        rank = {"explicit": 5, "inherent": 4, "partial": 3, "absent": 1, "unknown": 0}
        em = dict(keep.get("element_map") or {})
        if keep is not primary_doc:
            for k, v in em.items():
                if isinstance(v, dict) and v.get("quote") and not v.get("source_number"):
                    v["source_number"] = keep["number"]
        for m in others:
            for k, v in (m.get("element_map") or {}).items():
                if not isinstance(v, dict):
                    continue
                v = dict(v)
                if v.get("quote") and not v.get("source_number") and m["number"] != primary_doc["number"]:
                    v["source_number"] = m["number"]
                cur = em.get(k)
                if cur is None or rank.get(v.get("state"), 0) > rank.get((cur or {}).get("state"), 0):
                    em[k] = v
        if em:
            keep["element_map"] = em
        for f in ("title", "assignee_or_authors", "priority_date", "filing_date", "grant_date", "url"):
            if primary_doc.get(f):
                keep[f] = primary_doc[f]
        keep["pub_date"] = earliest(*[m.get("pub_date") for m in members])
        keep["number"] = primary_doc["number"]
        keep["country"] = primary_doc.get("country")
        keep["kind"] = primary_doc.get("kind")
        keep["type"] = primary_doc.get("type")
        keep["family"] = fam
        keep["verified"] = all(m.get("verified") for m in members)
        keep["verified_how"] = "; ".join(_uniq_list(m.get("verified_how") for m in members if m.get("verified_how")))
        keep.setdefault("merged_from", [])
        keep["merged_from"].extend(i for i in merged_ids if i)
        notes = [m.get("notes") for m in members if m.get("notes")]
        if notes:
            keep["notes"] = " | ".join(_uniq_list(notes))
        for i in merged_ids:
            if i:
                renames[i] = keep.get("id")
        res["findings"].append(finding("INFO", "family_merge", keep.get("id") or keep["number"],
                                       "merged %s into one reference (%s + family %s)"
                                       % (", ".join([keep.get("id") or "?"] + [i or "?" for i in merged_ids]),
                                          keep["number"], ", ".join(fam))))
        out.append(keep)
    for c in pa.get("combinations") or []:
        c["refs"] = _uniq_list(renames.get(x, x) for x in c.get("refs") or [])
    return out, renames


def _uniq_list(seq):
    out = []
    for x in seq:
        if x and x not in out:
            out.append(x)
    return out


# --------------------------------------------------------------------------- run


DEFAULTS = {"dir": "patent", "json": False, "no_audit": False, "offline": False, "dry_run": False,
            "no_merge": False, "today": None, "only": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    pa = load_prior_art(a.dir)
    res = new_result()
    refs = pa.get("references") or []
    cutoff = pa.get("cutoff_date")
    res["checks_run"] += ["number", "fetch", "title", "dates", "assignee"]
    only = set(a.only.split(",")) if a.only else None
    for ref in refs:
        if only and ref.get("id") not in only:
            continue
        rtype = ref.get("type")
        if rtype in ("npl", "web", "product") or (not ref.get("number") and (ref.get("doi") or ref.get("url"))):
            verify_npl_ref(ref, a, res)
        elif ref.get("number"):
            verify_patent_ref(ref, a, res)
        else:
            res["findings"].append(finding("WARN", "unverified", ref.get("id") or "?",
                                           "reference has no number, DOI, or URL; left verified: false"))
            ref["verified"] = False
    if not a.no_merge:
        refs, renames = merge_families(refs, pa, res)
        res["checks_run"].append("family")
    else:
        res["checks_skipped"].append({"check": "family", "reason": "--no-merge"})
    if cutoff:
        res["checks_run"].append("basis")
        for ref in refs:
            basis, note = compute_basis(ref, cutoff)
            old = ref.get("prior_art_basis")
            ref["prior_art_basis"] = basis
            if old and old != basis:
                res["findings"].append(finding("INFO", "basis_changed", ref.get("id") or "?",
                                               "prior_art_basis %s -> %s (%s)" % (old, basis, note)))
            if basis == "needs_evidence":
                res["findings"].append(finding("WARN", "needs_evidence", ref.get("id") or "?", note))
            if basis == "102(a)(1)" and ref.get("pub_date") and str(ref["pub_date"]) >= _minus_year(cutoff):
                res["findings"].append(finding("INFO", "grace_check", ref.get("id") or "?",
                                               "published within 1 year before cutoff: if this is the inventor's own "
                                               "disclosure (or derived from it), 102(b)(1) may except it"))
            if basis == "102(a)(2)" and ref.get("category") not in (None, "E"):
                res["findings"].append(finding("INFO", "category_hint", ref.get("id") or "?",
                                               "102(a)(2) art is usually category E (earlier filed, later published)"))
    else:
        res["checks_skipped"].append({"check": "basis", "reason": "prior-art.json has no cutoff_date"})
    if not os.environ.get("USPTO_ODP_API_KEY"):
        res["checks_skipped"].append({"check": "odp_cross_check", "reason": "USPTO_ODP_API_KEY not set"})
    for ref in refs:
        ref.pop("_app_no", None)
        ref.pop("_family_pubs", None)
    pa["references"] = refs
    if not a.dry_run:
        save_prior_art(a.dir, pa)
    ver = [r for r in refs if r.get("verified")]
    res["summary"] = {"references": len(refs), "verified": len(ver), "unverified": len(refs) - len(ver),
                      "cutoff_date": cutoff}
    for r in refs:
        res["text"].append("%-4s %-18s %-10s %-14s %s" % (r.get("id"), r.get("number") or r.get("doi") or r.get("url"),
                                                        "VERIFIED" if r.get("verified") else "UNVERIFIED",
                                                        r.get("prior_art_basis") or "-", (r.get("title") or "")[:70]))
    res["references"] = refs
    return finalize(res)


def _minus_year(d):
    from _dates import add_months
    return add_months(d, -12).isoformat()


def build_parser():
    p = argparse.ArgumentParser(prog="verify_refs.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p, network=True)
    p.add_argument("--dry-run", action="store_true", help="do not write prior-art.json")
    p.add_argument("--no-merge", action="store_true", help="do not merge publication + grant families")
    p.add_argument("--only", default=None, help="comma-separated reference ids to verify")
    p.add_argument("--today", default=None, help=argparse.SUPPRESS)
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
