#!/usr/bin/env python3
"""Build IDS data (PTO/SB/08 sections) from verified references.

Writes <dir>/draft/out/ids.json and ids.csv with four sections, as on form PTO/SB/08:
  us_patents        cite no., document number (US-9,457,709-B2), kind, issue date, first-named patentee
  us_publications   cite no., document number (US-20160144773-A1), kind, publication date, applicant
  foreign           cite no., country, number, kind, publication date, applicant, non_english,
                    translation_attached, relevance_statement
  npl               cite no., full citation (author, title, venue, date, pages/identifier)

Foreign columns (37 CFR 1.98(a)(3)):
  non_english           true / false / null (EP and WO: unknown unless the cached page was a
                        Google translation). It is NOT the SB/08 "T" box.
  translation_attached  the SB/08 "T" box: an English translation is attached. Default false;
                        set `translation_attached: true` on the reference only when one is attached
                        (a Google machine translation in the cache is not an attached translation).
  relevance_statement   for each non-English document, the concise explanation of relevance that
                        1.98(a)(3)(i) requires: the reference's `relevance_statement`, else a stub.

Unverified references are never listed; they are reported separately (excluded). Names come
from the cached record (first-named inventor for patentee/applicant, assignee as a fallback).
The script prints the item count and the IDS size-fee tiers (37 CFR 1.17(v): more than 50,
100, 200 cumulative items), with dollar amounts read from references/fees.md when present.

Examples:
    python3 scripts/ids.py
    python3 scripts/ids.py --include-family --json
    python3 scripts/ids.py --already-cited 40     # items cited in earlier IDSs (size fee is cumulative)

Exit codes: 0 ok, 1 nothing to list (no verified references), 2 bad input.
"""

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from normalize_number import normalize  # noqa: E402
from patent_fetch import ENGLISH_OFFICES, find_cached  # noqa: E402
from quote_check import load_record_for  # noqa: E402
from state import (UsageError, add_common, audit, cli_main, finalize, finding, load_prior_art,  # noqa: E402
                   new_result, sha256_path, to_namespace, utc_now, write_json)

SCHEMA_IDS = "patentassist/ids@1"
TIERS = (50, 100, 200)
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def form_date(iso):
    """ISO -> MM-DD-YYYY as printed on PTO/SB/08."""
    if not iso or len(str(iso)) < 10:
        return iso
    y, m, d = str(iso)[:10].split("-")
    return "%s-%s-%s" % (m, d, y)


def sb08_number(norm):
    """Document number as written on SB/08: US-9,457,709-B2 / US-20160144773-A1."""
    if norm["doc_type"] == "application_pub":
        return "US-%s-%s" % (norm["number"], norm["kind"] or "")
    n = norm["number"]
    m = re.match(r"^(RE|D|PP|H|T)?(\d+)$", n)
    if m:
        pre, digits = m.groups()
        n = (pre or "") + "{:,}".format(int(digits))
    return "US-%s%s" % (n, ("-" + norm["kind"]) if norm.get("kind") else "")


def first_name(rec, ref):
    if rec:
        inv = rec.get("inventors") or []
        if inv:
            return inv[0]
        asg = [a for a in rec.get("assignees") or [] if a and a.lower() != "individual"]
        if asg:
            return asg[0]
    v = ref.get("assignee_or_authors") or ""
    return re.split(r";", v)[0].strip() or None


def applicant_name(rec, ref):
    if rec:
        asg = [a for a in rec.get("assignees") or [] if a and a.lower() != "individual"]
        inv = rec.get("inventors") or []
        if asg:
            return asg[0]
        if inv:
            return inv[0]
    v = ref.get("assignee_or_authors") or ""
    return re.split(r";", v)[0].strip() or None


def npl_citation(ref, rec):
    if rec and rec.get("citation"):
        base = rec["citation"]
    else:
        au = ref.get("assignee_or_authors")
        parts = [au, ('"%s"' % ref["title"]) if ref.get("title") else None, ref.get("venue"), ref.get("pub_date"),
                 ("doi:" + ref["doi"]) if ref.get("doi") else None, ref.get("url") if not ref.get("doi") else None]
        base = ", ".join(p for p in parts if p)
    if ref.get("evidence_url") and ref["evidence_url"] not in base:
        base += " (archived: %s)" % ref["evidence_url"]
    return base


def relevance_stub(number):
    return ("[concise explanation of relevance of %s, as presently understood (37 CFR 1.98(a)(3)(i)); draft it "
            "from the chart, or cite an English-language search report that explains it]" % number)


def non_english_flag(country):
    if country in ENGLISH_OFFICES:
        return False
    if country in ("EP", "WO"):
        return None  # depends on the publication language; check the document
    return True


def fee_tiers(skill_root):
    """Return (amounts_by_tier or None, source) from references/fees.md."""
    path = os.path.join(skill_root, "references", "fees.md")
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    amounts = {}
    for blk in re.findall(r"```json\s*(.*?)```", text, re.S):
        try:
            data = json.loads(blk)
        except ValueError:
            continue
        fees = data.get("fees", data)
        for t in TIERS:
            f = fees.get("ids_size_over_%d" % t)
            if isinstance(f, dict):
                amounts[t] = {"large": f.get("large"), "small": f.get("small"), "micro": f.get("micro"),
                              "cfr": f.get("cfr")}
    if not amounts:
        for line in text.splitlines():
            if "1.17(v)" in line and "|" in line:
                cells = [c.strip() for c in line.strip("|").split("|")]
                m = re.search(r"exceed\s+(\d+)", line)
                if m and len(cells) >= 4:
                    amounts[int(m.group(1))] = {"large": cells[-3], "small": cells[-2], "micro": cells[-1],
                                                "cfr": cells[1]}
    return (amounts or None), "references/fees.md"


def tier_for(n):
    hit = [t for t in TIERS if n > t]
    return hit[-1] if hit else 0


DEFAULTS = {"dir": "patent", "json": False, "no_audit": False, "include_family": False, "already_cited": 0,
            "out": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    pa = load_prior_art(a.dir)
    res = new_result()
    res["checks_run"].append("verified_only")
    sections = {"us_patents": [], "us_publications": [], "foreign": [], "npl": []}
    excluded = []
    seen = set()

    def add_doc(number, ref, rec, from_family=False):
        norm = normalize(number)
        if not norm.get("ok"):
            res["findings"].append(finding("WARN", "bad_number", ref.get("id") or "?", "cannot parse %s; not listed" % number))
            return
        key = norm["canonical"]
        if key in seen:
            return
        seen.add(key)
        if rec is None or (rec.get("number") and rec.get("number") != norm["canonical"] and from_family):
            _, rec2 = find_cached(a.dir, number)
            rec = rec2 or (None if from_family else rec)
        row = {"ref": ref.get("id"), "family_of": ref.get("number") if from_family else None,
               "prior_art_basis": ref.get("prior_art_basis"), "category": ref.get("category")}
        if norm["country"] == "US" and norm["doc_type"] in ("patent", "design", "plant", "reissue"):
            date = (rec or {}).get("grant_date") or (ref.get("grant_date") if not from_family else None)
            row.update({"document_number": sb08_number(norm), "kind": norm.get("kind") or (rec or {}).get("kind"),
                        "issue_date": date, "issue_date_form": form_date(date),
                        "patentee": first_name(rec, ref if not from_family else {})})
            sections["us_patents"].append(row)
        elif norm["country"] == "US" and norm["doc_type"] == "application_pub":
            date = (rec or {}).get("publication_date") or (ref.get("pub_date") if not from_family else None)
            row.update({"document_number": sb08_number(norm), "kind": norm.get("kind"),
                        "publication_date": date, "publication_date_form": form_date(date),
                        "applicant": first_name(rec, ref if not from_family else {})})
            sections["us_publications"].append(row)
        else:
            date = (rec or {}).get("publication_date") or (ref.get("pub_date") if not from_family else None)
            ne = non_english_flag(norm["country"])
            if ne is None and any("machine translation from" in str(n) for n in (rec or {}).get("notes") or []):
                ne = True  # EP/WO published in German or French (patent_fetch saw Google's translation)
            attached = bool(ref.get("translation_attached")) and not from_family
            row.update({"country": norm["country"], "number": norm["number"], "kind": norm.get("kind"),
                        "document_number": "%s-%s-%s" % (norm["country"], norm["number"], norm.get("kind") or ""),
                        "publication_date": date, "publication_date_form": form_date(date),
                        "applicant": applicant_name(rec, ref if not from_family else {}),
                        "non_english": ne, "translation_attached": attached})
            if ne:
                given = (ref.get("relevance_statement") or "").strip() if not from_family else ""
                row["relevance_statement"] = given or relevance_stub(norm["canonical"])
                row["note"] = ("non-English: the IDS needs a concise explanation of relevance (37 CFR 1.98(a)(3)(i)) "
                               "and a copy of any English translation you have or can readily get (1.98(a)(3)(ii)). "
                               "Tick the SB/08 T box only if a translation is attached.")
                if not given:
                    res["findings"].append(finding("WARN", "relevance_statement_needed", ref.get("id") or number,
                                                   "%s is non-English: write its concise explanation of relevance "
                                                   "(37 CFR 1.98(a)(3)(i)); a stub is in ids.json"
                                                   % norm["canonical"]))
            elif ne is None:
                row["note"] = "check the publication language (non-English documents need 37 CFR 1.98(a)(3) items)"
            sections["foreign"].append(row)
        missing = [k for k in ("issue_date", "publication_date", "patentee", "applicant") if k in row and not row[k]]
        if missing:
            res["findings"].append(finding("WARN", "missing_field", ref.get("id") or number,
                                           "%s: %s missing (fetch it with patent_fetch.py)" % (number, ", ".join(missing))))

    for ref in pa.get("references") or []:
        if not ref.get("verified"):
            excluded.append({"ref": ref.get("id"), "number": ref.get("number") or ref.get("doi") or ref.get("url"),
                             "reason": "unverified"})
            continue
        if ref.get("prior_art_basis") == "not_prior_art":
            res["findings"].append(finding("INFO", "not_prior_art", ref.get("id") or "?",
                                           "listed, but dated after the cutoff; decide whether it is material"))
        if ref.get("type") in ("npl", "web", "product") or not ref.get("number"):
            rec = load_record_for(a.dir, None, ref)
            sections["npl"].append({"ref": ref.get("id"), "citation": npl_citation(ref, rec),
                                    "pub_date": ref.get("pub_date"), "prior_art_basis": ref.get("prior_art_basis"),
                                    "category": ref.get("category")})
            continue
        _, rec = find_cached(a.dir, ref["number"])
        add_doc(ref["number"], ref, rec)
        fam = ref.get("family") or []
        if fam and a.include_family:
            for f in fam:
                add_doc(f, ref, None, from_family=True)
        elif fam:
            res["findings"].append(finding("INFO", "family_not_listed", ref.get("id") or "?",
                                           "family members not listed: %s (use --include-family)" % ", ".join(fam)))
    cite = 0
    for sec in ("us_patents", "us_publications", "foreign", "npl"):
        for row in sections[sec]:
            cite += 1
            row["cite_no"] = cite
    count = cite
    cumulative = count + int(a.already_cited or 0)
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    amounts, src = fee_tiers(skill_root)
    tier = tier_for(cumulative)
    out_dir = a.out or os.path.join(a.dir, "draft", "out")
    os.makedirs(out_dir, exist_ok=True)
    doc = {"schema": SCHEMA_IDS, "generated": utc_now(), "count": count, "already_cited": int(a.already_cited or 0),
           "cumulative": cumulative, "size_fee_tier": tier, "size_fee_amounts": amounts, "sections": sections,
           "excluded": excluded,
           "notes": ["Verified references only. Unverified references are in `excluded` and must not be cited "
                     "until verified.",
                     "The IDS size fee (37 CFR 1.17(v)) counts items cumulatively across all IDSs in the application; "
                     "each document is one item."]}
    jpath = os.path.join(out_dir, "ids.json")
    cpath = os.path.join(out_dir, "ids.csv")
    write_json(jpath, doc)
    with open(cpath, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["section", "cite_no", "document_number", "country", "kind", "date", "name", "non_english",
                    "translation_attached", "relevance_statement", "citation", "ref", "prior_art_basis"])
        for sec in ("us_patents", "us_publications", "foreign", "npl"):
            for r in sections[sec]:
                row = [sec, r["cite_no"], r.get("document_number", ""), r.get("country", "US" if sec.startswith("us") else ""),
                       r.get("kind") or "", r.get("issue_date_form") or r.get("publication_date_form") or r.get("pub_date") or "",
                       r.get("patentee") or r.get("applicant") or "",
                       "" if sec != "foreign" or r.get("non_english") is None else ("Y" if r.get("non_english") else "N"),
                       "" if sec != "foreign" else ("Y" if r.get("translation_attached") else "N"),
                       r.get("relevance_statement") or "",
                       r.get("citation", ""), r.get("ref") or "", r.get("prior_art_basis") or ""]
                w.writerow([_safe_cell(x) for x in row])
    for p in (jpath, cpath):
        audit(a.dir, "export", a.no_audit, path=os.path.relpath(p, a.dir), sha256=sha256_path(p))
    res["ids"] = doc
    res["paths"] = {"json": jpath, "csv": cpath}
    t = res["text"]
    t.append("IDS items: %d (US patents %d, US publications %d, foreign %d, NPL %d); excluded unverified: %d"
             % (count, len(sections["us_patents"]), len(sections["us_publications"]), len(sections["foreign"]),
                len(sections["npl"]), len(excluded)))
    for e in excluded:
        t.append("  excluded %s %s (%s)" % (e["ref"], e["number"], e["reason"]))
    t.append("Cumulative items in the application: %d%s" % (
        cumulative, " (including %d already cited)" % a.already_cited if a.already_cited else ""))
    for th in TIERS:
        amt = ""
        if amounts and th in amounts:
            x = amounts[th]
            amt = "  $%s (%s; same for all entity sizes)" % (x.get("large"), x.get("cfr")) if \
                x.get("large") == x.get("small") == x.get("micro") else \
                "  large $%s / small $%s / micro $%s (%s)" % (x.get("large"), x.get("small"), x.get("micro"), x.get("cfr"))
        t.append("  size-fee tier > %d items%s%s" % (th, amt, "   <- applies" if tier == th else ""))
    if tier == 0:
        t.append("  No IDS size fee at %d items (fee starts above 50)." % cumulative)
    else:
        t.append("  Tier amounts are cumulative: subtract any tier already paid.")
    if not amounts:
        t.append("  (fee amounts not found in references/fees.md; tiers only)")
    t.append("Wrote %s and %s" % (jpath, cpath))
    res["summary"] = {"count": count, "cumulative": cumulative, "tier": tier, "excluded": len(excluded)}
    if count == 0:
        res["findings"].append(finding("BLOCK", "empty", "ids", "no verified references to list"))
    return finalize(res)


def _safe_cell(v):
    s = "" if v is None else str(v)
    return "'" + s if s.startswith(FORMULA_START) else s


def build_parser():
    p = argparse.ArgumentParser(prog="ids.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p)
    p.add_argument("--include-family", action="store_true", help="also list family members of each reference")
    p.add_argument("--already-cited", type=int, default=0, help="items already cited in earlier IDSs")
    p.add_argument("--out", default=None, help="output folder (default <dir>/draft/out)")
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
