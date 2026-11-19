#!/usr/bin/env python3
"""Fetch non-patent literature metadata and web-page dates into cache/NPL-<slug>.json.

Examples:
    python3 scripts/npl_fetch.py doi 10.1364/OE.17.011638
    python3 scripts/npl_fetch.py search "single-photon synchronous detection"
    python3 scripts/npl_fetch.py arxiv 2509.20517
    python3 scripts/npl_fetch.py wayback "http://www.ubergizmo.com/2013/02/dora-bike-helmet-has-indicators/"

Sources (keyless, see references/sources-and-apis.md):
  doi     Crossref /works/{DOI}, then OpenAlex /works/doi:{DOI} (also when Crossref has no abstract)
  search  OpenAlex /works?search=... (ranked by OpenAlex relevance), then Crossref
          /works?query.bibliographic=... for anything OpenAlex missed. Each result prints the first
          sentence of its abstract. A result is cached only when its title matches the query
          (title lookup, similarity >= 0.85); otherwise nothing is cached: fetch one with `doi`.
          (the query leaves this machine: send only titles or approved abstracted terms)
  arxiv   export.arxiv.org Atom API (1 request per 3 s)
  wayback Wayback CDX API: earliest capture with HTTP 200 (proves the page existed no later
          than that time); falls back to the availability API

Records use the patentassist/patent@1 shape with doc_type "npl" or "web". The abstract is cached
(OpenAlex abstract_inverted_index rebuilt to text; Crossref JATS markup stripped) so quote_check.py
can check NPL quotes against it.
Exit codes: 0 ok, 1 nothing found, 2 bad input, 3 network/source failure.
"""

import argparse
import difflib
import html
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from patent_fetch import cache_dir, http_request, safe_name  # noqa: E402
from state import (SCHEMA_PATENT, SourceError, UsageError, add_common, audit, cli_main,  # noqa: E402
                   finalize, finding, new_result, read_json, to_namespace, utc_now, write_json)

CROSSREF = "https://api.crossref.org/works"
OPENALEX = "https://api.openalex.org/works"
ARXIV = "https://export.arxiv.org/api/query"
CDX = "https://web.archive.org/cdx/search/cdx"
AVAIL = "https://archive.org/wayback/available"


# --------------------------------------------------------------------------- text similarity


def tokens(s):
    s = (s or "").lower()
    s = s.replace("’", "'").replace("&", " and ")
    return re.findall(r"[a-z0-9]+", s)


def token_ratio(a, b):
    """Fuzzy title similarity in [0, 1]: token-sort ratio, raised to 0.9 when one title's tokens
    are all inside the other's and the shorter has at least 5 tokens (truncated titles)."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    sa, sb = " ".join(sorted(ta)), " ".join(sorted(tb))
    score = difflib.SequenceMatcher(None, sa, sb).ratio()
    seq = difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio()
    score = max(score, seq)
    small, big = (set(ta), set(tb)) if len(set(ta)) <= len(set(tb)) else (set(tb), set(ta))
    if len(small) >= 5 and small <= big:
        score = max(score, 0.9)
    return round(score, 4)


# --------------------------------------------------------------------------- helpers


def slug(s, maxlen=80):
    s = re.sub(r"^https?://", "", (s or "").strip().lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:maxlen].strip("-") or "unnamed"


def npl_path(dirpath, stem):
    return os.path.join(cache_dir(dirpath), safe_name(stem) + ".json")


def clean_doi(doi):
    d = (doi or "").strip()
    d = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", d, flags=re.I)
    if not re.match(r"^10\.\d{4,9}/\S+$", d):
        raise UsageError("not a DOI: %r" % doi)
    return d


def _strip_tags(s):
    if not s:
        return s
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def strip_jats(s):
    """Crossref abstracts are JATS XML (<jats:p>, <jats:italic>, a <jats:title>Abstract</jats:title>
    heading). Drop the heading, turn tags into spaces, unescape entities, collapse whitespace."""
    if not s:
        return None
    s = re.sub(r"<(?:jats:)?title\b[^>]*>.*?</(?:jats:)?title>", " ", s, flags=re.S | re.I)
    s = re.sub(r"</?(?:jats:)?(?:italic|bold|sup|sub|sc|underline)\b[^>]*>", "", s, flags=re.I)
    s = _strip_tags(s)
    s = re.sub(r"\s+([,.;:)])", r"\1", s)
    return s or None


def first_sentence(s, limit=220):
    s = (s or "").strip()
    if not s:
        return None
    m = re.search(r"^(.+?[.!?])(?:\s+[A-Z(\[]|$)", s)
    out = m.group(1) if m else s
    return out if len(out) <= limit else out[:limit - 1].rstrip() + "\u2026"


def _date_parts(dp):
    try:
        parts = dp["date-parts"][0]
    except (KeyError, IndexError, TypeError):
        return None
    if not parts or parts[0] is None:
        return None
    y = int(parts[0])
    m = int(parts[1]) if len(parts) > 1 and parts[1] else None
    d = int(parts[2]) if len(parts) > 2 and parts[2] else None
    if m and d:
        return "%04d-%02d-%02d" % (y, m, d)
    if m:
        return "%04d-%02d" % (y, m)
    return "%04d" % y


def base_record(doc_type, stem):
    return {"schema": SCHEMA_PATENT, "number": stem, "country": None, "kind": None, "doc_type": doc_type,
            "title": None, "abstract": None, "text": None, "authors": [], "assignees": [], "inventors": [],
            "venue": None, "doi": None, "pub_date": None, "publication_date": None, "priority_date": None,
            "filing_date": None, "grant_date": None, "family": [], "claims": [], "description": [],
            "citations": {"backward": [], "forward": []}, "url": None, "source": None, "fetched": utc_now(),
            "notes": []}


def citation_string(rec):
    au = rec.get("authors") or []
    who = au[0] + (" et al." if len(au) > 1 else "") if au else None
    parts = [p for p in [who, '"%s"' % rec["title"] if rec.get("title") else None, rec.get("venue"),
                         rec.get("pub_date"), ("doi:" + rec["doi"]) if rec.get("doi") else None,
                         rec.get("url") if not rec.get("doi") else None] if p]
    return ", ".join(parts)


def _get_json(url):
    status, body, _ = http_request(url, headers={"Accept": "application/json"})
    if status != 200:
        return status, None
    try:
        return status, json.loads(body.decode("utf-8"))
    except ValueError:
        return status, None


def from_crossref(item):
    stem = "NPL-doi-" + slug(item.get("DOI"))
    rec = base_record("npl", stem)
    rec["doi"] = item.get("DOI")
    titles = item.get("title") or []
    rec["title"] = _strip_tags(titles[0]) if titles else None
    authors = []
    for a in item.get("author") or []:
        nm = " ".join(x for x in [a.get("given"), a.get("family")] if x) or a.get("name")
        if nm:
            authors.append(nm)
    rec["authors"] = authors
    ct = item.get("container-title") or []
    rec["venue"] = ct[0] if ct else item.get("publisher")
    date = None
    for k in ("published-print", "published-online", "issued", "published", "created"):
        date = _date_parts(item.get(k)) if item.get(k) else None
        if date:
            break
    rec["pub_date"] = rec["publication_date"] = date
    rec["abstract"] = strip_jats(item.get("abstract"))
    if rec["abstract"]:
        rec["abstract_source"] = "crossref"
    rec["url"] = item.get("URL") or ("https://doi.org/" + rec["doi"] if rec["doi"] else None)
    rec["source"] = "crossref"
    rec["work_type"] = item.get("type")
    if date and len(date) < 10:
        rec["notes"].append("Crossref gives only %s precision for the date." % ("year" if len(date) == 4 else "month"))
    return rec


def _openalex_abstract(inv):
    """Rebuild text from OpenAlex's abstract_inverted_index {word: [positions]}."""
    if not isinstance(inv, dict):
        return None
    pos = {}
    for word, idxs in inv.items():
        for i in idxs or []:
            if isinstance(i, int):
                pos[i] = word
    if not pos:
        return None
    return re.sub(r"\s+", " ", " ".join(pos[i] for i in sorted(pos))).strip() or None


def _no_abstract_note(rec):
    if not rec.get("abstract") and not rec.get("text"):
        rec["notes"].append("No abstract or text in Crossref or OpenAlex: quotes from this record cannot be checked "
                            "until text is added (e.g. paste the abstract into the record's text field from the "
                            "publisher page).")


def from_openalex(w):
    doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
    stem = "NPL-doi-" + slug(doi) if doi else "NPL-openalex-" + slug((w.get("id") or "").rsplit("/", 1)[-1])
    rec = base_record("npl", stem)
    rec["doi"] = doi
    rec["title"] = w.get("title") or w.get("display_name")
    rec["authors"] = [((a.get("author") or {}).get("display_name")) for a in (w.get("authorships") or [])
                      if (a.get("author") or {}).get("display_name")]
    src = ((w.get("primary_location") or {}).get("source") or {})
    rec["venue"] = src.get("display_name")
    rec["pub_date"] = rec["publication_date"] = w.get("publication_date")
    rec["abstract"] = _openalex_abstract(w.get("abstract_inverted_index"))
    if rec["abstract"]:
        rec["abstract_source"] = "openalex"
    rec["relevance"] = w.get("relevance_score")
    rec["url"] = ("https://doi.org/" + doi) if doi else w.get("id")
    rec["source"] = "openalex"
    rec["openalex_id"] = w.get("id")
    rec["work_type"] = w.get("type")
    return rec


# --------------------------------------------------------------------------- commands


def cmd_doi(a, res):
    doi = clean_doi(a.target)
    stem = "NPL-doi-" + slug(doi)
    path = npl_path(a.dir, stem)
    if os.path.exists(path) and not a.force:
        rec = read_json(path)
        res["record"], res["path"], res["status"] = rec, path, "cached"
        return
    if a.offline:
        res["findings"].append(finding("WARN", "not_cached", doi, "offline and not in cache"))
        res["exit_code"] = 3
        return
    rec = None
    status, data = _get_json(CROSSREF + "/" + urllib.parse.quote(doi, safe="/"))
    res["checks_run"].append("crossref")
    if data and data.get("message"):
        rec = from_crossref(data["message"])
        if not rec.get("abstract"):
            status2, w = _get_json(OPENALEX + "/doi:" + urllib.parse.quote(doi, safe="/"))
            res["checks_run"].append("openalex (abstract)")
            if w and w.get("id"):
                ab = _openalex_abstract(w.get("abstract_inverted_index"))
                rec["openalex_id"] = w.get("id")
                if ab:
                    rec["abstract"] = ab
                    rec["abstract_source"] = "openalex"
    else:
        status2, w = _get_json(OPENALEX + "/doi:" + urllib.parse.quote(doi, safe="/"))
        res["checks_run"].append("openalex")
        if w and w.get("id"):
            rec = from_openalex(w)
    if not rec:
        audit(a.dir, "fetch", a.no_audit, number=doi, source="crossref+openalex", ok=False)
        res["findings"].append(finding("BLOCK", "not_found", doi, "DOI not found in Crossref or OpenAlex"))
        return
    rec["number"] = stem
    rec.pop("relevance", None)
    rec["citation"] = citation_string(rec)
    _no_abstract_note(rec)
    write_json(path, rec)
    audit(a.dir, "fetch", a.no_audit, number=stem, source=rec["source"], ok=True)
    res["record"], res["path"], res["status"] = rec, path, "fetched"


def cmd_search(a, res):
    q = a.target.strip()
    if len(q) < 3:
        raise UsageError("search needs some title words")
    if a.offline:
        raise UsageError("search needs the network (no --offline)")
    cands = []
    status, data = _get_json(OPENALEX + "?" + urllib.parse.urlencode({"search": q, "per-page": a.rows}))
    res["checks_run"].append("openalex")
    for w in (data or {}).get("results") or []:
        rec = from_openalex(w)
        if rec.get("title"):
            cands.append(rec)
    status, data = _get_json(CROSSREF + "?" + urllib.parse.urlencode({"query.bibliographic": q, "rows": a.rows}))
    res["checks_run"].append("crossref")
    for item in ((data or {}).get("message") or {}).get("items") or []:
        rec = from_crossref(item)
        if not rec.get("title"):
            continue
        same = next((c for c in cands if c.get("doi") and c["doi"].lower() == (rec.get("doi") or "").lower()), None)
        if same:
            if not same.get("abstract") and rec.get("abstract"):
                same["abstract"], same["abstract_source"] = rec["abstract"], "crossref"
            continue
        rec["relevance"] = item.get("score")
        cands.append(rec)
    # order: OpenAlex results in OpenAlex relevance order, then Crossref-only results in Crossref order
    for c in cands:
        c["title_score"] = token_ratio(q, c["title"])
    audit(a.dir, "query", a.no_audit, source="openalex+crossref", query=q, hits=len(cands))
    res["candidates"] = [{"rank": i + 1, "title": c["title"], "doi": c.get("doi"), "pub_date": c.get("pub_date"),
                          "authors": c.get("authors")[:3], "venue": c.get("venue"), "source": c["source"],
                          "relevance": c.get("relevance"), "title_score": c["title_score"],
                          "abstract_first_sentence": first_sentence(c.get("abstract"))}
                         for i, c in enumerate(cands)]
    for c in res["candidates"]:
        rel = ("%.1f" % c["relevance"]) if isinstance(c["relevance"], (int, float)) else "-"
        res["text"].append("%2d. [%s rel %s] %s  %s  doi:%s" % (c["rank"], c["source"], rel, c["pub_date"],
                                                                c["title"], c["doi"]))
        res["text"].append("      %s" % (c["abstract_first_sentence"] or "(no abstract)"))
    if not cands:
        res["findings"].append(finding("BLOCK", "not_found", q, "no results in OpenAlex or Crossref"))
        return
    by_title = sorted(cands, key=lambda c: -c["title_score"])
    best = by_title[0]
    tie = (len(by_title) > 1 and by_title[1]["title_score"] >= 0.85
           and best["title_score"] - by_title[1]["title_score"] < 0.05
           and (best.get("doi") or "").lower() != (by_title[1].get("doi") or "").lower())
    if best["title_score"] >= 0.85 and not tie:
        for k in ("title_score", "relevance", "score"):
            best.pop(k, None)
        best["citation"] = citation_string(best)
        _no_abstract_note(best)
        path = npl_path(a.dir, best["number"])
        write_json(path, best)
        res["record"], res["path"], res["status"] = best, path, "fetched"
        res["text"].append("Title match cached -> %s" % path)
        return
    res["status"] = "candidates_only"
    if tie:
        res["text"].append("Search results (nothing cached): several titles match closely (e.g. conference and journal "
                           "versions). Pick the right one and fetch it with: npl_fetch.py doi <DOI>")
    else:
        res["text"].append("Search results (nothing cached); fetch one with: npl_fetch.py doi <DOI>")


def cmd_arxiv(a, res):
    aid = re.sub(r"^(?:arxiv:|https?://arxiv\.org/(?:abs|pdf)/)", "", a.target.strip(), flags=re.I)
    aid = re.sub(r"\.pdf$", "", aid)
    if not re.match(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$", aid):
        raise UsageError("not an arXiv id: %r" % a.target)
    stem = "NPL-arxiv-" + slug(aid)
    path = npl_path(a.dir, stem)
    if os.path.exists(path) and not a.force:
        res["record"], res["path"], res["status"] = read_json(path), path, "cached"
        return
    if a.offline:
        res["findings"].append(finding("WARN", "not_cached", aid, "offline and not in cache"))
        res["exit_code"] = 3
        return
    status, body, _ = http_request(ARXIV + "?" + urllib.parse.urlencode({"id_list": aid, "max_results": 1}),
                                   spacing=3.0)
    res["checks_run"].append("arxiv")
    if status != 200:
        raise SourceError("arXiv HTTP %d" % status)
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(body)
    entry = root.find("a:entry", ns)
    if entry is None or entry.find("a:title", ns) is None or (entry.findtext("a:id", "", ns) or "").endswith("api/errors"):
        res["findings"].append(finding("BLOCK", "not_found", aid, "arXiv has no entry for this id"))
        audit(a.dir, "fetch", a.no_audit, number=stem, source="arxiv", ok=False)
        return
    rec = base_record("npl", stem)
    rec["title"] = re.sub(r"\s+", " ", entry.findtext("a:title", "", ns)).strip()
    rec["abstract"] = re.sub(r"\s+", " ", entry.findtext("a:summary", "", ns)).strip()
    rec["authors"] = [re.sub(r"\s+", " ", (au.findtext("a:name", "", ns) or "")).strip()
                      for au in entry.findall("a:author", ns)]
    published = (entry.findtext("a:published", "", ns) or "")[:10] or None
    rec["pub_date"] = rec["publication_date"] = published
    rec["updated"] = (entry.findtext("a:updated", "", ns) or "")[:10] or None
    rec["doi"] = entry.findtext("arxiv:doi", None, ns)
    rec["venue"] = "arXiv"
    rec["arxiv_id"] = aid
    rec["url"] = entry.findtext("a:id", None, ns) or ("https://arxiv.org/abs/" + aid)
    rec["source"] = "arxiv"
    rec["notes"].append("pub_date is the first version's submission date; later versions may differ in content.")
    rec["citation"] = citation_string(rec)
    write_json(path, rec)
    audit(a.dir, "fetch", a.no_audit, number=stem, source="arxiv", ok=True)
    res["record"], res["path"], res["status"] = rec, path, "fetched"


def cmd_wayback(a, res):
    url = a.target.strip()
    if not re.match(r"^(https?://)?[^\s/]+\.[^\s]+", url):
        raise UsageError("not a URL: %r" % url)
    stem = "NPL-web-" + slug(url)
    path = npl_path(a.dir, stem)
    if os.path.exists(path) and not a.force:
        res["record"], res["path"], res["status"] = read_json(path), path, "cached"
        return
    if a.offline:
        res["findings"].append(finding("WARN", "not_cached", url, "offline and not in cache"))
        res["exit_code"] = 3
        return
    q = {"url": url, "output": "json", "limit": 5, "filter": "statuscode:200"}
    status, body, _ = http_request(CDX + "?" + urllib.parse.urlencode(q))
    res["checks_run"].append("wayback_cdx")
    rows = []
    if status == 200 and body.strip():
        try:
            data = json.loads(body.decode("utf-8"))
            if data and isinstance(data[0], list) and data[0][:2] == ["urlkey", "timestamp"]:
                hdr = data[0]
                rows = [dict(zip(hdr, r)) for r in data[1:]]
        except ValueError:
            rows = []
    capture = None
    if rows:
        r0 = rows[0]
        capture = {"timestamp": r0["timestamp"], "original": r0.get("original"), "status": r0.get("statuscode"),
                   "source": "wayback_cdx"}
    else:
        status, data = _get_json(AVAIL + "?" + urllib.parse.urlencode({"url": url, "timestamp": "19960101"}))
        res["checks_run"].append("wayback_available")
        closest = ((data or {}).get("archived_snapshots") or {}).get("closest") or {}
        if closest.get("available") and str(closest.get("status")) == "200":
            capture = {"timestamp": closest["timestamp"], "original": url, "status": "200",
                       "source": "wayback_available"}
    rec = base_record("web", stem)
    rec["url"] = url
    rec["source"] = "wayback"
    if not capture:
        rec["notes"].append("No Wayback capture with HTTP 200; the page date needs other evidence.")
        rec["pub_date"] = None
        write_json(path, rec)
        audit(a.dir, "fetch", a.no_audit, number=stem, source="wayback", ok=False)
        res["findings"].append(finding("WARN", "no_capture", url, "no archived capture with HTTP 200"))
        res["record"], res["path"], res["status"] = rec, path, "no_capture"
        return
    ts = capture["timestamp"]
    date = "%s-%s-%s" % (ts[:4], ts[4:6], ts[6:8])
    rec["earliest_capture"] = {"date": date, "timestamp": ts, "source": capture["source"],
                               "capture_url": "https://web.archive.org/web/%s/%s" % (ts, capture["original"] or url)}
    rec["pub_date"] = rec["publication_date"] = date
    rec["date_basis"] = "earliest_wayback_capture"
    rec["notes"].append("Wayback capture proves the page existed no later than %s; the content at that capture "
                        "must be checked to match what is cited." % date)
    rec["citation"] = "%s (archived %s: %s)" % (url, date, rec["earliest_capture"]["capture_url"])
    write_json(path, rec)
    audit(a.dir, "fetch", a.no_audit, number=stem, source=capture["source"], ok=True)
    res["record"], res["path"], res["status"] = rec, path, "fetched"


COMMANDS = {"doi": cmd_doi, "search": cmd_search, "arxiv": cmd_arxiv, "wayback": cmd_wayback}
DEFAULTS = {"command": None, "target": None, "dir": "patent", "json": False, "no_audit": False,
            "offline": False, "force": False, "rows": 5}


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.command not in COMMANDS:
        raise UsageError("command must be one of %s" % ", ".join(COMMANDS))
    if not a.target:
        raise UsageError("missing argument")
    os.makedirs(cache_dir(a.dir), exist_ok=True)
    res = new_result()
    res["command"] = a.command
    COMMANDS[a.command](a, res)
    rec = res.get("record")
    if rec and a.command != "search":
        res["text"].insert(0, "%s  %s  %s  %s  -> %s" % (res.get("status"), rec.get("pub_date"), rec.get("title") or
                                                     rec.get("url"), rec.get("source"), res.get("path")))
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="npl_fetch.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p, network=True)
    sp = p.add_subparsers(dest="command")
    for name, helptext in (("doi", "fetch by DOI"), ("search", "search title words"),
                           ("arxiv", "fetch by arXiv id"), ("wayback", "earliest Wayback capture of a URL")):
        s = sp.add_parser(name, help=helptext)
        add_common(s, sub=True, network=True)
        s.add_argument("target")
        s.add_argument("--force", action="store_true", help="re-fetch even if cached")
        if name == "search":
            s.add_argument("--rows", type=int, default=5)
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
