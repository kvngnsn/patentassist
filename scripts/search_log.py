#!/usr/bin/env python3
"""Search log: record queries in prior-art.json, show coverage, plan and diff re-runs.

Examples:
    python3 scripts/search_log.py plan --source google_patents_web --query 'helmet "turn signal" wireless' \\
        --elements E2,E3                                   # status planned (Q1), nothing has run yet
    python3 scripts/search_log.py add --id Q1 --hits 14 --screened 10 \\
        --results US9457709B2,US20160144773A1              # completes the planned Q1
    python3 scripts/search_log.py add --source google_patents_web \\
        --query 'helmet "turn signal" wireless' --hits 14 --screened 10 --elements E2,E3 \\
        --results US9457709B2,US20160144773A1              # log and run in one step
    python3 scripts/search_log.py add --id Q2 --hits 9 --tool-rewrote \\
        --ran-as 'helmet turn signal'                      # the search tool dropped operators/terms
    python3 scripts/search_log.py list
    python3 scripts/search_log.py coverage
    python3 scripts/search_log.py rerun-plan --since 2026-11-18
    # ... re-run each query, then record it with --rerun-of Q1 and its --results ...
    python3 scripts/search_log.py diff --since 2026-11-18

Each query gets the next Q-id. `plan` records a query before it runs (status "planned", no hits);
`add --id Qn` completes it with the hits and results (status "run"). `coverage` counts only queries
that ran and lists planned ones separately.

When the search tool rewrites a query (drops `site:` or a term, or says it changed it), record what
actually ran with `--ran-as "..."` and flag it with `--tool-rewrote`; the planned text stays in
`query`. Every run query records `summary_untrusted: true` by default: take candidate numbers only
from result titles and URLs, never from the tool's prose summary (it invents numbers, owners, and
content). `--no-summary-untrusted` is for sources with no prose summary at all.

 `--results` stores the document numbers the query returned (or
the ones screened), normalized, so a later re-run can be diffed: `diff` prints only numbers not
returned by any earlier run of the same query and not already in references / read_not_cited.
A re-run is linked to its original by --rerun-of, or automatically when the source and the
query text match an earlier entry.

Every `add` appends a `query` line to audit.jsonl. Queries leave the machine only when the
model runs them; this script never sends anything.
Exit codes: 0 ok, 2 bad input.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _dates import parse_date  # noqa: E402
from normalize_number import normalize  # noqa: E402
from state import (UsageError, add_common, audit, cli_main, finalize, finding, load_prior_art,  # noqa: E402
                   new_result, save_prior_art, to_namespace, today_iso)


def _qnum(qid):
    m = re.match(r"^Q(\d+)$", qid or "")
    return int(m.group(1)) if m else 0


def _norm_query(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def _norm_source(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")


def _canon(n):
    r = normalize(n)
    return r["canonical"] if r.get("ok") else n.strip()


def _split(s):
    if s is None:
        return []
    if isinstance(s, list):
        return [x.strip() for x in s if str(x).strip()]
    return [x.strip() for x in re.split(r"[,\n;]", s) if x.strip()]


def _family_key(n):
    """Kind-less key so a re-run returning the B2 does not count the A1 as 'new' twice."""
    r = normalize(n)
    if r.get("ok") and r.get("number"):
        return "%s%s" % (r["country"], r["number"])
    return n


def root_of(q, by_id):
    seen = set()
    while q.get("rerun_of") and q["rerun_of"] in by_id and q["id"] not in seen:
        seen.add(q["id"])
        q = by_id[q["rerun_of"]]
    return q


SUMMARY_NOTE = ("Take candidate numbers only from result titles and URLs; the search tool's prose summary is not "
                "evidence of numbers, owners, or content.")


def is_planned(q):
    return q.get("status") == "planned"


def _ran(qs):
    return [q for q in qs if not is_planned(q)]


def _next_qid(queries):
    return "Q%d" % (max([_qnum(q.get("id")) for q in queries] or [0]) + 1)


def _check_elements(pa, els, qid, res):
    known = {e.get("id") for e in pa.get("elements") or []}
    for e in els:
        if known and e not in known:
            res["findings"].append(finding("WARN", "unknown_element", qid, "element %s is not in prior-art.json elements" % e))


def cmd_plan(a, pa, res):
    if not a.source or not a.query:
        raise UsageError("plan needs --source and --query")
    queries = pa.setdefault("queries", [])
    qid = _next_qid(queries)
    els = _split(a.elements)
    _check_elements(pa, els, qid, res)
    q = {"id": qid, "status": "planned", "source": _norm_source(a.source), "query": a.query.strip(),
         "planned": today_iso(a.date or a.today)}
    if els:
        q["elements"] = els
    if a.note:
        q["note"] = a.note
    dup = [x for x in queries if is_planned(x) and x.get("source") == q["source"]
           and _norm_query(x.get("query")) == _norm_query(q["query"])]
    if dup:
        res["findings"].append(finding("WARN", "duplicate_plan", qid, "same source and query already planned as %s"
                                       % dup[0]["id"]))
    queries.append(q)
    save_prior_art(a.dir, pa)
    audit(a.dir, "note", a.no_audit, action="plan_query", id=qid, source=q["source"], query=q["query"],
          elements=els or None)
    res["query"] = q
    res["text"].append("%s planned: [%s] %s%s" % (qid, q["source"], q["query"],
                                                  ("  elements " + ",".join(els)) if els else ""))
    res["text"].append("After running it: search_log.py add --id %s --hits N [--results ...] [--ran-as '...' "
                       "--tool-rewrote]" % qid)


def _fill_run(q, a, res, qid):
    """Run fields shared by add and add --id."""
    q["date"] = today_iso(a.date or a.today)
    q["hits"] = a.hits
    if a.screened is not None:
        q["screened"] = a.screened
    results = [_canon(n) for n in _split(a.results)]
    if results:
        q["results"] = results
    if a.ran_as and a.ran_as.strip():
        if _norm_query(a.ran_as) != _norm_query(q["query"]):
            q["ran_as"] = a.ran_as.strip()
        else:
            q.pop("ran_as", None)
    if a.tool_rewrote:
        q["tool_rewrote"] = True
        if not q.get("ran_as"):
            res["findings"].append(finding("WARN", "rewrite_unrecorded", qid,
                                           "the tool rewrote the query: record what actually ran with --ran-as"))
    q["summary_untrusted"] = bool(a.summary_untrusted)
    if a.note:
        q["note"] = a.note


def cmd_add(a, pa, res):
    if a.hits is None or a.hits < 0:
        raise UsageError("--hits must be a non-negative integer")
    if a.screened is not None and a.screened < 0:
        raise UsageError("--screened must be non-negative")
    queries = pa.setdefault("queries", [])
    if a.id:
        q = next((x for x in queries if x.get("id") == a.id), None)
        if q is None:
            raise UsageError("--id %s: no such query (plan it first, or omit --id)" % a.id)
        if not is_planned(q):
            raise UsageError("%s already ran on %s; to re-run it, add a new query with --rerun-of %s"
                             % (a.id, q.get("date"), a.id))
        if a.source and _norm_source(a.source) != q["source"]:
            raise UsageError("%s was planned for source %s; log a run on %s as a new query"
                             % (a.id, q["source"], _norm_source(a.source)))
        if a.query and _norm_query(a.query) != _norm_query(q["query"]):
            raise UsageError("%s was planned as %r; record the text that actually ran with --ran-as"
                             % (a.id, q["query"]))
        if a.elements:
            els = _split(a.elements)
            _check_elements(pa, els, a.id, res)
            q["elements"] = els
        if a.rerun_of:
            raise UsageError("--rerun-of cannot be combined with --id")
        q["status"] = "run"
        qid = a.id
        _fill_run(q, a, res, qid)
    else:
        if not a.source or not a.query:
            raise UsageError("--source and --query are required (or --id Qn to complete a planned query)")
        qid = _next_qid(queries)
        els = _split(a.elements)
        _check_elements(pa, els, qid, res)
        q = {"id": qid, "status": "run", "source": _norm_source(a.source), "query": a.query.strip()}
        if els:
            q["elements"] = els
        _fill_run(q, a, res, qid)
        date = q["date"]
        if a.rerun_of:
            ids = {x.get("id") for x in _ran(queries)}
            if a.rerun_of not in ids:
                raise UsageError("--rerun-of %s: no such query that has run" % a.rerun_of)
            q["rerun_of"] = a.rerun_of
        else:
            prev = [x for x in _ran(queries) if _norm_source(x.get("source")) == q["source"]
                    and _norm_query(x.get("query")) == _norm_query(q["query"]) and (x.get("date") or "") <= date]
            if prev:
                q["rerun_of"] = prev[-1]["id"]
                res["findings"].append(finding("INFO", "rerun_linked", qid, "same source and query as %s; linked as "
                                               "a re-run" % prev[-1]["id"]))
        queries.append(q)
    save_prior_art(a.dir, pa)
    audit(a.dir, "query", a.no_audit, id=qid, source=q["source"], query=q["query"], hits=a.hits,
          screened=a.screened, elements=q.get("elements") or None, rerun_of=q.get("rerun_of"),
          ran_as=q.get("ran_as"), tool_rewrote=q.get("tool_rewrote"))
    res["query"] = q
    res["text"].append("%s recorded: [%s] %s (hits %d%s)" % (qid, q["source"], q["query"], a.hits,
                                                           ", screened %d" % a.screened if a.screened is not None else ""))
    if q.get("ran_as"):
        res["text"].append("    ran as: %s%s" % (q["ran_as"], "  (tool rewrote the query)" if q.get("tool_rewrote") else ""))
    if q.get("summary_untrusted"):
        res["text"].append("    note: " + SUMMARY_NOTE)


def cmd_list(a, pa, res):
    qs = pa.get("queries") or []
    res["queries"] = qs
    if not qs:
        res["text"].append("No queries recorded.")
    for q in qs:
        if is_planned(q):
            res["text"].append("%-4s %s  %-22s PLANNED (not run)  elements=%-12s %s" % (
                q.get("id"), q.get("planned"), q.get("source"), ",".join(q.get("elements") or []) or "-",
                q.get("query")))
            continue
        res["text"].append("%-4s %s  %-22s hits=%-5s screened=%-5s elements=%-12s %s%s%s" % (
            q.get("id"), q.get("date"), q.get("source"), q.get("hits"), q.get("screened", "-"),
            ",".join(q.get("elements") or []) or "-", q.get("query"),
            ("  (re-run of %s)" % q["rerun_of"]) if q.get("rerun_of") else "",
            ("  [ran as: %s%s]" % (q["ran_as"], "; tool rewrote" if q.get("tool_rewrote") else "")) if q.get("ran_as")
            else ("  [tool rewrote]" if q.get("tool_rewrote") else "")))
    ran = _ran(qs)
    res["summary"] = {"queries": len(qs), "run": len(ran), "planned": len(qs) - len(ran),
                      "hits": sum(int(q.get("hits") or 0) for q in ran),
                      "screened": sum(int(q.get("screened") or 0) for q in ran)}


def coverage_matrix(pa):
    """Elements x sources counts of queries that ran (planned queries are not counted)."""
    qs = _ran(pa.get("queries") or [])
    sources = []
    for q in qs:
        if q.get("source") not in sources:
            sources.append(q.get("source"))
    elements = [e.get("id") for e in pa.get("elements") or []]
    for q in pa.get("queries") or []:
        for e in q.get("elements") or []:
            if e not in elements:
                elements.append(e)
    m = {e: {s: 0 for s in sources} for e in elements}
    for q in qs:
        for e in q.get("elements") or []:
            m[e][q.get("source")] += 1
    return elements, sources, m


def cmd_coverage(a, pa, res):
    res["checks_run"].append("coverage")
    elements, sources, m = coverage_matrix(pa)
    if not elements:
        res["checks_skipped"].append({"check": "coverage", "reason": "no elements in prior-art.json"})
        res["text"].append("No elements defined.")
        return
    essential = {e.get("id"): e.get("essential", True) for e in pa.get("elements") or []}
    planned_qs = [q for q in pa.get("queries") or [] if is_planned(q)]
    planned_by_el = {e: [q["id"] for q in planned_qs if e in (q.get("elements") or [])] for e in elements}
    w = max([len(s) for s in sources] + [5])
    res["text"].append("element  " + "  ".join(s.rjust(min(w, 22))[:22] for s in sources) + "  total  planned")
    never, single = [], []
    for e in elements:
        row = [m[e][s] for s in sources]
        tot = sum(row)
        res["text"].append("%-8s " % e + "  ".join(str(x).rjust(min(w, 22))[:22] for x in row) + "  %5d  %7d"
                           % (tot, len(planned_by_el[e])))
        if tot == 0:
            never.append(e)
            lvl = "WARN" if essential.get(e, True) else "INFO"
            msg = "no recorded query that ran targets this element"
            if planned_by_el[e]:
                msg += " (planned, not run: %s)" % ",".join(planned_by_el[e])
            res["findings"].append(finding(lvl, "never_searched", e, msg))
        elif sum(1 for x in row if x) == 1 and len(sources) > 1:
            single.append(e)
            res["findings"].append(finding("INFO", "single_source", e, "searched in only one source"))
    untagged = [q.get("id") for q in _ran(pa.get("queries") or []) if not q.get("elements")]
    if untagged:
        res["findings"].append(finding("INFO", "untagged_queries", ",".join(untagged),
                                       "queries without --elements do not count toward coverage"))
    if planned_qs:
        res["findings"].append(finding("INFO", "planned_not_run", ",".join(q["id"] for q in planned_qs),
                                       "%d planned quer%s not run yet (not counted above)"
                                       % (len(planned_qs), "y" if len(planned_qs) == 1 else "ies")))
    rewritten = [q for q in _ran(pa.get("queries") or []) if q.get("tool_rewrote") or q.get("ran_as")]
    for q in rewritten:
        res["findings"].append(finding("INFO", "rewritten", q["id"], "counted, but ran as %r, not as planned %r; "
                                       "check that the element's terms survived" % (q.get("ran_as") or "?",
                                                                                     q.get("query"))))
    ran_count = len(_ran(pa.get("queries") or []))
    res["text"].append("Queries run: %d; planned, not run: %d" % (ran_count, len(planned_qs)))
    res["coverage"] = {"elements": elements, "sources": sources, "matrix": m, "never_searched": never,
                       "single_source": single, "planned": planned_by_el,
                       "planned_not_run": [q["id"] for q in planned_qs]}
    res["summary"] = {"elements": len(elements), "never_searched": len(never), "sources": len(sources),
                      "run": ran_count, "planned": len(planned_qs)}


def _latest_runs(qs):
    qs = _ran(qs)
    by_id = {q.get("id"): q for q in qs}
    latest = {}
    for q in qs:
        root = root_of(q, by_id)
        cur = latest.get(root["id"])
        if cur is None or (q.get("date") or "") >= (cur.get("date") or ""):
            latest[root["id"]] = q
    return by_id, latest


def cmd_rerun_plan(a, pa, res):
    if not a.since:
        raise UsageError("rerun-plan needs --since YYYY-MM-DD")
    since = parse_date(a.since).isoformat()
    qs = pa.get("queries") or []
    by_id, latest = _latest_runs(qs)
    plan = []
    for root_id, q in latest.items():
        if (q.get("date") or "") > since:
            continue  # already re-run after the cutoff
        root = by_id[root_id]
        plan.append({"rerun_of": root_id, "last_run": q.get("id"), "last_date": q.get("date"),
                     "source": root.get("source"), "query": root.get("query"),
                     "elements": root.get("elements") or [], "results_recorded": len(q.get("results") or [])})
    plan.sort(key=lambda p: _qnum(p["rerun_of"]))
    never = [q.get("id") for q in qs if is_planned(q)]
    if never:
        res["findings"].append(finding("INFO", "planned_not_run", ",".join(never),
                                       "planned but never run; run them and complete with add --id"))
    res["plan"] = plan
    res["since"] = since
    if not plan:
        res["text"].append("Nothing to re-run: every query has a run after %s." % since)
    for p in plan:
        res["text"].append("%s [%s] %s   (last run %s on %s, %d results recorded)" % (
            p["rerun_of"], p["source"], p["query"], p["last_run"], p["last_date"], p["results_recorded"]))
        res["text"].append("    record with: search_log.py add --source %s --query %s --hits N --results <numbers> "
                           "--rerun-of %s%s" % (p["source"], _shell_quote(p["query"]), p["rerun_of"],
                                                (" --elements " + ",".join(p["elements"])) if p["elements"] else ""))
    if plan:
        res["text"].append("Tip: limit each re-run to documents published after %s (for example the source's date "
                           "filter) so only new art comes back." % since)
        res["text"].append("Then run: search_log.py diff --since %s" % since)
    res["summary"] = {"to_rerun": len(plan)}


def _shell_quote(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def cmd_diff(a, pa, res):
    if not a.since:
        raise UsageError("diff needs --since YYYY-MM-DD")
    since = parse_date(a.since).isoformat()
    qs = _ran(pa.get("queries") or [])
    by_id = {q.get("id"): q for q in qs}
    known = set()
    for r in pa.get("references") or []:
        for n in [r.get("number")] + list(r.get("family") or []):
            if n:
                known.add(_family_key(n))
    for r in pa.get("read_not_cited") or []:
        if r.get("number"):
            known.add(_family_key(r["number"]))
    out = []
    reruns = [q for q in qs if q.get("rerun_of") and (q.get("date") or "") >= since]
    for q in reruns:
        root = root_of(q, by_id)
        chain = [x for x in qs if root_of(x, by_id)["id"] == root["id"] and x is not q
                 and ((x.get("date") or "") < (q.get("date") or "") or _qnum(x["id"]) < _qnum(q["id"]))]
        before = set()
        for x in chain:
            before |= {_family_key(n) for n in x.get("results") or []}
        new = [n for n in q.get("results") or [] if _family_key(n) not in before and _family_key(n) not in known]
        if not q.get("results"):
            res["findings"].append(finding("WARN", "no_results_recorded", q["id"],
                                           "re-run has no --results; cannot diff"))
        out.append({"id": q["id"], "rerun_of": root["id"], "source": q.get("source"), "query": q.get("query"),
                    "date": q.get("date"), "new": new})
    res["diff"] = out
    allnew = []
    for d in out:
        for n in d["new"]:
            if n not in allnew:
                allnew.append(n)
    if not reruns:
        res["text"].append("No re-runs recorded on or after %s (use add --rerun-of Qn)." % since)
    for d in out:
        res["text"].append("%s (re-run of %s, %s): %s" % (d["id"], d["rerun_of"], d["date"],
                                                         ", ".join(d["new"]) if d["new"] else "nothing new"))
    res["new_numbers"] = allnew
    res["summary"] = {"reruns": len(out), "new": len(allnew)}


COMMANDS = {"plan": cmd_plan, "add": cmd_add, "list": cmd_list, "coverage": cmd_coverage,
            "rerun-plan": cmd_rerun_plan, "diff": cmd_diff}
DEFAULTS = {"command": None, "dir": "patent", "json": False, "no_audit": False, "source": None, "query": None,
            "hits": None, "screened": None, "elements": None, "results": None, "rerun_of": None, "date": None,
            "note": None, "since": None, "today": None, "id": None, "ran_as": None, "tool_rewrote": False,
            "summary_untrusted": True}


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.command not in COMMANDS:
        raise UsageError("command must be one of %s" % ", ".join(COMMANDS))
    pa = load_prior_art(a.dir)
    res = new_result()
    res["command"] = a.command
    COMMANDS[a.command](a, pa, res)
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="search_log.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p)
    sp = p.add_subparsers(dest="command")
    s = sp.add_parser("plan", help="record a query before it runs (status planned)")
    add_common(s, sub=True)
    s.add_argument("--source", required=True)
    s.add_argument("--query", required=True)
    s.add_argument("--elements", default=None, help="comma-separated element ids, e.g. E1,E2")
    s.add_argument("--date", default=None, help="plan date (default today)")
    s.add_argument("--note", default=None)
    s.add_argument("--today", default=None, help=argparse.SUPPRESS)
    s = sp.add_parser("add", help="record a query that ran (or complete a planned one with --id)")
    add_common(s, sub=True)
    s.add_argument("--id", default=None, help="planned Q-id to complete")
    s.add_argument("--source", default=None, help="required unless --id")
    s.add_argument("--query", default=None, help="required unless --id")
    s.add_argument("--hits", type=int, required=True)
    s.add_argument("--ran-as", default=None, help="the query text that actually ran, if it differs")
    s.add_argument("--tool-rewrote", action="store_true", help="the search tool changed the query")
    s.add_argument("--summary-untrusted", action=argparse.BooleanOptionalAction, default=True,
                   help="the tool's prose summary is not evidence")
    s.add_argument("--screened", type=int, default=None)
    s.add_argument("--elements", default=None, help="comma-separated element ids, e.g. E1,E2")
    s.add_argument("--results", default=None, help="comma-separated document numbers returned/screened")
    s.add_argument("--rerun-of", default=None, help="Q-id this query re-runs")
    s.add_argument("--date", default=None, help="run date (default today)")
    s.add_argument("--note", default=None)
    s.add_argument("--today", default=None, help=argparse.SUPPRESS)
    for name, h in (("list", "list queries"), ("coverage", "elements x sources matrix")):
        x = sp.add_parser(name, help=h)
        add_common(x, sub=True)
    for name, h in (("rerun-plan", "queries to replay since a date"), ("diff", "new numbers from re-runs")):
        x = sp.add_parser(name, help=h)
        add_common(x, sub=True)
        x.add_argument("--since", required=True)
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
