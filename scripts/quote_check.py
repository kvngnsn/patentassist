#!/usr/bin/env python3
"""Confirm every quote is verbatim in the cached source text; fill pinpoints.

Checks prior-art.json element_map quotes and charts/*.json cell quotes against the cached
record (claims + description + abstract; NPL: abstract + text). Matching ignores case and
normalizes whitespace, quote marks, dashes, soft hyphens, and spaces before punctuation; an
ellipsis (... or the single character) in a quote splits it into parts that must appear in
order in the same passage. Nothing else is forgiven.

On success the pinpoint is written: the paragraph label ([0018] or p17), "claim N", or
"abstract". On failure: BLOCK with the closest passage (difflib) so the quote can be corrected.
Quote text is never changed by this script.

Examples:
    python3 scripts/quote_check.py
    python3 scripts/quote_check.py --chart charts/r1.json --dry-run --json

Limit: US grants have no printed paragraph numbers (they print column:line). Their pinpoints
are Google-text paragraph numbers pN. When the grant PDF is cached (colline.py fetch N), a found
quote with a pN pinpoint is also placed on the printed page with colline.locate_in_cache (offline,
never the network): a high-confidence result is written to `pinpoint_colline` ("col. 4, ll. 10-22");
a low one is reported, not written. Without PyMuPDF that step is skipped (ledger: "PyMuPDF missing").

Machine translations: a record whose notes say "machine translation" gets one INFO per reference
(machine_translation): quotes from it are Google's translation and are marked
[machine translation – review] in rendered charts.
Exit codes: 0 all quotes found, 1 a quote was not found or its source is not cached, 2 bad input.
"""

import argparse
import difflib
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from patent_fetch import cache_path, find_cached  # noqa: E402
from state import (SCHEMA_CHART, UsageError, add_common, audit, check_schema, cli_main, finalize,  # noqa: E402
                   finding, load_prior_art, new_result, read_json, save_prior_art, to_namespace, write_json)

_TRANS = {}
for ch in "“”„‟″«»":
    _TRANS[ord(ch)] = '"'
for ch in "‘’‚‛′`´":
    _TRANS[ord(ch)] = "'"
for ch in "‐‑‒–—―−﹘﹣－":
    _TRANS[ord(ch)] = "-"
for ch in "      　\t\r\n":
    _TRANS[ord(ch)] = " "
_TRANS[0x00AD] = None  # soft hyphen
_TRANS[0x200B] = None  # zero-width space
_LIG = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}

ELLIPSIS_RE = re.compile(r"\s*(?:\.\s*\.\s*\.|…)\s*")
SYNTHETIC_PIN = re.compile(r"^p\d+$")
GRANT_TYPES = ("patent", "design", "plant", "reissue")


def is_machine_translated(rec):
    return any("machine translation" in str(n).lower() for n in (rec or {}).get("notes") or [])


def norm(s):
    s = (s or "").translate(_TRANS)
    for k, v in _LIG.items():
        s = s.replace(k, v)
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:!?)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s.strip()


def segments(rec):
    """[(label, text)] searchable passages, description first (preferred pinpoints), then abstract, claims."""
    segs = []
    for p in rec.get("description") or []:
        segs.append((p.get("label") or p.get("pid"), p.get("text") or ""))
    if rec.get("abstract"):
        segs.append(("abstract", rec["abstract"]))
    for c in rec.get("claims") or []:
        segs.append(("claim %s" % c.get("num"), c.get("text") or ""))
    if rec.get("text"):
        txt = rec["text"]
        if isinstance(txt, list):
            for i, t in enumerate(txt, 1):
                segs.append(("text p%d" % i, t))
        else:
            for i, t in enumerate([x for x in re.split(r"\n\s*\n", txt) if x.strip()], 1):
                segs.append(("text p%d" % i, t))
    if rec.get("title") and rec.get("doc_type") in ("npl", "web"):
        segs.append(("title", rec["title"]))
    return segs


def find_quote(quote, segs):
    """Return list of labels where the (normalized) quote appears."""
    parts = [norm(p) for p in ELLIPSIS_RE.split(quote or "") if norm(p)]
    if not parts:
        return []
    hits = []
    for label, text in segs:
        t = norm(text)
        pos = 0
        ok = True
        for p in parts:
            i = t.find(p, pos)
            if i < 0:
                ok = False
                break
            pos = i + len(p)
        if ok:
            hits.append(label)
    return hits


def closest(quote, segs, limit=1):
    """Best fuzzy window (original wording) for a quote that was not found."""
    q = norm(ELLIPSIS_RE.sub(" ", quote or ""))
    qn = len(q.split())
    if not qn:
        return []
    qset = set(q.split())
    best = []
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(q)
    for label, text in segs:
        words = (text or "").split()
        if not words:
            continue
        nwords = [norm(w) for w in words]
        if not qset & set(nwords):
            continue
        sizes = sorted(set([qn, max(1, qn - 2), qn + 2]))
        for size in sizes:
            for i in range(0, max(1, len(words) - size + 1)):
                window = " ".join(nwords[i:i + size])
                sm.set_seq1(window)
                if sm.real_quick_ratio() < 0.5 or sm.quick_ratio() < 0.5:
                    continue
                r = sm.ratio()
                if not best or r > best[-1][0] or len(best) < limit:
                    best.append((r, label, " ".join(words[i:i + size])))
                    best.sort(key=lambda x: -x[0])
                    best = best[:limit]
    return [{"ratio": round(r, 3), "pinpoint": lab, "snippet": snip} for r, lab, snip in best]


# --------------------------------------------------------------------------- record lookup


def load_record_for(dirpath, number=None, ref=None, cache_by_key=None):
    key = number or (ref or {}).get("cache") or (ref or {}).get("doi") or (ref or {}).get("url")
    if cache_by_key is not None and key in cache_by_key:
        return cache_by_key[key]
    rec = None
    if number:
        _, rec = find_cached(dirpath, number)
        if rec is None and str(number).startswith("NPL-") and os.path.exists(cache_path(dirpath, number)):
            rec = read_json(cache_path(dirpath, number))
    if rec is None and ref:
        stems = []
        if ref.get("cache"):
            stems.append(ref["cache"])
        if ref.get("doi"):
            from npl_fetch import slug
            stems.append("NPL-doi-" + slug(re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", ref["doi"], flags=re.I)))
        if ref.get("arxiv_id"):
            from npl_fetch import slug
            stems.append("NPL-arxiv-" + slug(ref["arxiv_id"]))
        if ref.get("url"):
            from npl_fetch import slug
            stems.append("NPL-web-" + slug(ref["url"]))
        for s in stems:
            p = cache_path(dirpath, s)
            if os.path.exists(p):
                rec = read_json(p)
                break
    if cache_by_key is not None:
        cache_by_key[key] = rec
    return rec


# --------------------------------------------------------------------------- checking


def _para_text(rec, label):
    for p in rec.get("description") or []:
        if p.get("label") == label or p.get("pid") == label:
            return p.get("text")
    return None


def colline_pinpoint(entry, where, rec, pin, res, a, cst):
    """F08: place a found US-grant quote (synthetic pN pinpoint) on the cached grant PDF."""
    if cst.get("disabled"):
        return
    cst["candidates"] += 1
    try:
        import colline  # lazy: needs PyMuPDF only when a grant PDF is actually read
        loc = colline.locate_in_cache(a.dir, rec["number"], entry.get("quote"), context=_para_text(rec, pin))
    except UsageError as e:
        cst["disabled"] = "PyMuPDF missing (pip3 install pymupdf)" if "PyMuPDF" in str(e) else str(e)
        return
    if not loc.get("found") and not loc.get("pdf"):
        cst["no_pdf"].add(rec["number"])
        return
    cst["located"] += 1
    if loc.get("found") and loc.get("confidence") == "high":
        old = entry.get("pinpoint_colline")
        if old != loc["pinpoint"]:
            entry["pinpoint_colline"] = loc["pinpoint"]
            if old:
                res["findings"].append(finding("INFO", "colline_changed", where, "%s -> %s" % (old, loc["pinpoint"])))
        cst["filled"] += 1
    elif loc.get("found"):
        res["findings"].append(finding("INFO", "colline_low", where,
                                       "col:line %s is low confidence (%s); not written. Check the PDF or run "
                                       "colline.py annotate" % (loc["pinpoint"], "; ".join(loc.get("reasons") or []))))
    else:
        if entry.pop("pinpoint_colline", None) is not None:
            res["findings"].append(finding("WARN", "colline_removed", where,
                                           "quote not located in the grant PDF; stale pinpoint_colline removed"))
        else:
            res["findings"].append(finding("INFO", "colline_not_found", where, "%s: %s" % (rec["number"],
                                                                                          loc.get("reason"))))


def check_entry(entry, where, rec, number, res, a, grant_noted, cst=None):
    quote = entry.get("quote")
    if rec is None:
        res["findings"].append(finding("BLOCK", "no_cache", where,
                                       "source %s is not cached; run patent_fetch.py fetch %s (or npl_fetch.py) first"
                                       % (number, number)))
        res["summary"]["no_cache"] += 1
        return False
    segs = segments(rec)
    hits = find_quote(quote, segs)
    if cst is not None and is_machine_translated(rec) and rec.get("number") not in cst["mt_noted"]:
        cst["mt_noted"].add(rec.get("number"))
        res["findings"].append(finding("INFO", "machine_translation", rec.get("number") or number,
                                       "text of %s is Google machine translation: quotes from it are marked "
                                       "[machine translation – review]; get a human translation before relying on "
                                       "them" % (rec.get("number") or number)))
    if hits:
        pin = hits[0]
        old = entry.get("pinpoint")
        if old != pin:
            if old:
                res["findings"].append(finding("INFO", "pinpoint_set", where, "pinpoint %s -> %s" % (old, pin)))
            entry["pinpoint"] = pin
        if len(hits) > 1:
            entry["pinpoint_also"] = hits[1:6]
        elif "pinpoint_also" in entry:
            entry.pop("pinpoint_also")
        if (rec.get("paragraph_labels") == "synthesized" and pin.startswith("p") and rec.get("number")
                and rec["number"] not in grant_noted):
            grant_noted.add(rec["number"])
            us_grant = rec.get("country") == "US" and rec.get("doc_type") in ("patent", "design", "plant", "reissue")
            translated = any("machine translation" in str(n) for n in rec.get("notes") or [])
            where_to_cite = ("column:line from the PDF" if us_grant else
                             "page:line (or the printed paragraph) of the original-language PDF; the quote is "
                             "Google's machine translation" if translated else
                             "page:line or the printed paragraph from the PDF")
            res["findings"].append(finding("INFO", "synthesized_pinpoint", rec["number"],
                                           "paragraph labels for %s are synthesized (pN); in filings, cite %s"
                                           % (rec["number"], where_to_cite)))
        if (cst is not None and SYNTHETIC_PIN.match(pin) and rec.get("country") == "US"
                and rec.get("doc_type") in GRANT_TYPES and rec.get("number")):
            colline_pinpoint(entry, where, rec, pin, res, a, cst)
        res["summary"]["found"] += 1
        audit(a.dir, "quote", a.no_audit, where=where, number=rec.get("number"), result="found", pinpoint=pin,
              pinpoint_colline=entry.get("pinpoint_colline"))
        return True
    near = closest(quote, segs)
    msg = "quote not found verbatim in %s" % (rec.get("number") or number)
    if near:
        msg += "; closest (%.2f) at %s: \"%s\"" % (near[0]["ratio"], near[0]["pinpoint"], near[0]["snippet"])
        entry_hint = near[0]
    else:
        msg += "; no similar passage"
        entry_hint = None
    res["findings"].append(finding("BLOCK", "quote_not_found", where, msg))
    res.setdefault("suggestions", []).append({"where": where, "quote": quote, "closest": entry_hint})
    res["summary"]["not_found"] += 1
    audit(a.dir, "quote", a.no_audit, where=where, number=rec.get("number") or number, result="not_found")
    return False


DEFAULTS = {"dir": "patent", "json": False, "no_audit": False, "dry_run": False, "chart": None,
            "skip_prior_art": False, "skip_charts": False}


def run(args):
    a = to_namespace(args, DEFAULTS)
    res = new_result()
    res["summary"] = {"checked": 0, "found": 0, "not_found": 0, "no_cache": 0}
    cache_by_key = {}
    grant_noted = set()
    cst = {"disabled": None, "candidates": 0, "located": 0, "filled": 0, "no_pdf": set(), "mt_noted": set()}
    pa = load_prior_art(a.dir, required=False)
    refs_by_id = {r.get("id"): r for r in (pa or {}).get("references") or []}

    if pa is not None and not a.skip_prior_art and not a.chart:
        res["checks_run"].append("prior-art element_map quotes")
        changed = False
        for ref in pa.get("references") or []:
            for el, entry in sorted((ref.get("element_map") or {}).items()):
                if not isinstance(entry, dict) or not entry.get("quote"):
                    continue
                number = entry.get("source_number") or ref.get("number")
                rec = load_record_for(a.dir, number, ref, cache_by_key)
                before = dict(entry)
                res["summary"]["checked"] += 1
                check_entry(entry, "prior-art %s.%s" % (ref.get("id"), el), rec, number or ref.get("doi") or ref.get("url"),
                            res, a, grant_noted, cst)
                if entry != before:
                    changed = True
        if changed and not a.dry_run:
            save_prior_art(a.dir, pa)
    elif pa is None:
        res["checks_skipped"].append({"check": "prior-art element_map quotes", "reason": "no prior-art.json"})

    chart_files = [a.chart] if a.chart else ([] if a.skip_charts else sorted(glob.glob(os.path.join(a.dir, "charts", "*.json"))))
    if chart_files:
        res["checks_run"].append("chart cell quotes")
    elif not a.skip_charts:
        res["checks_skipped"].append({"check": "chart cell quotes", "reason": "no charts/*.json"})
    for cf in chart_files:
        path = cf if os.path.exists(cf) else os.path.join(a.dir, cf)
        if not os.path.exists(path):
            raise UsageError("chart not found: %s" % cf)
        chart = check_schema(read_json(path), SCHEMA_CHART, path)
        chart_refs = {r.get("id"): r for r in chart.get("refs") or []}
        changed = False
        for i, cell in enumerate(chart.get("cells") or []):
            if not cell.get("quote"):
                continue
            rid = cell.get("ref")
            cref = chart_refs.get(rid) or {}
            pref = refs_by_id.get(rid) or {}
            number = cell.get("source_number") or cref.get("number") or pref.get("number")
            rec = load_record_for(a.dir, number, cref or pref, cache_by_key)
            before = dict(cell)
            res["summary"]["checked"] += 1
            check_entry(cell, "%s cell %d (%s x %s)" % (os.path.basename(path), i, cell.get("element"), rid),
                        rec, number, res, a, grant_noted, cst)
            if cell != before:
                changed = True
        if changed and not a.dry_run:
            write_json(path, chart)
    _colline_ledger(res, cst)
    s = res["summary"]
    res["text"].append("Quotes checked: %d, found: %d, not found: %d, source not cached: %d"
                       % (s["checked"], s["found"], s["not_found"], s["no_cache"]))
    if cst["filled"]:
        res["text"].append("col:line pinpoints written (pinpoint_colline): %d" % cst["filled"])
    return finalize(res)


def _colline_ledger(res, cst):
    check = "colline pinpoints (US grants)"
    for n in sorted(cst["no_pdf"]):
        res["findings"].append(finding("INFO", "grant_pdf_not_cached", n, "no cached grant PDF, so no col:line "
                                       "pinpoint; run colline.py fetch %s, then quote_check.py again" % n))
    res["summary"]["colline_filled"] = cst["filled"]
    if cst["disabled"]:
        res["checks_skipped"].append({"check": check, "reason": cst["disabled"]})
    elif not cst["candidates"]:
        res["checks_skipped"].append({"check": check, "reason": "no found US-grant quote with a synthetic pN pinpoint"})
    elif not cst["located"]:
        res["checks_skipped"].append({"check": check, "reason": "no grant PDF cached (colline.py fetch NUMBER)"})
    else:
        res["checks_run"].append(check)


def build_parser():
    p = argparse.ArgumentParser(prog="quote_check.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p)
    p.add_argument("--chart", default=None, help="check only this chart file")
    p.add_argument("--skip-charts", action="store_true")
    p.add_argument("--skip-prior-art", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="report only; do not write pinpoints")
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
