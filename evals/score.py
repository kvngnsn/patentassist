#!/usr/bin/env python3
"""Score a patentassist run against an eval case (evals/README.md).

    python3 evals/score.py --case /private/case.json --run /private/matter
    python3 evals/score.py --set lite --runs RUNS_ROOT          # every evals/lite/*.json; run dir RUNS_ROOT/<id>[/patent]
    options: [--online] [--k 10,25] [--json]

A run directory is the matter folder the skill wrote (state.json, prior-art.json, cache/, charts/, draft/).

Hard metrics (must be exactly 0 in every set):
  fabricated_refs     references in prior-art.json that verify_refs.py finds do not exist or do not match
                      (not_found, bad_number, number/kind/title/assignee/author mismatch)
  fabricated_quotes   quotes in prior-art.json and charts that quote_check.py cannot find verbatim
                      (quote_not_found) in the cached text
  cutoff_violations   references cited as prior art that were published after the case cutoff and are not
                      102(a)(2) art (or are 102(a)(2) art filed after the cutoff)
  Each also reports how many items could not be checked (no cache, offline), which never counts as 0.

Recall: recall@k of truth.references (and truth.applied / truth.examiner_cited when present) in the run's
ranked references (prior-art.json order, R1 first), matching kind-less numbers and, when truth.family_ok
is true, family members listed in the run's cache records.

Set-specific: lite compares state.json phases.lite.verdict with truth.verdict; draft runs check_package.py
and compares truth.expect (blocking, ready_to_export, references_verified, quotes_found, chart_blocks).

Offline by default (cache only). Exit codes: 0 every hard metric 0 and every expectation met, 1 otherwise,
2 usage or input error.
"""

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

FABRICATED_REF_CODES = {"not_found", "bad_number", "number_mismatch", "kind_mismatch", "title_mismatch",
                        "assignee_mismatch", "author_mismatch", "application_number"}


class UsageError(Exception):
    pass


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        raise UsageError("cannot read %s: %s" % (path, e))


def _kindless(num):
    import normalize_number
    r = normalize_number.normalize(num)
    canon = r.get("canonical") if r.get("ok") else re.sub(r"[^A-Z0-9]", "", str(num).upper())
    return normalize_number.kindless(canon)


def _quiet(fn, args):
    """Run a script's run(args) without letting it print."""
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        return fn(args)


# --------------------------------------------------------------------------- hard metrics

def fabricated_refs(run_dir, online=False):
    import verify_refs
    try:
        res = _quiet(verify_refs.run, {"dir": run_dir, "offline": not online, "dry_run": True, "no_audit": True})
    except Exception as e:  # noqa: BLE001 - report, never crash the scorer
        return {"value": None, "unchecked": None, "error": "%s: %s" % (e.__class__.__name__, e)}
    bad = sorted(set(f.get("where") for f in res.get("findings", [])
                     if f.get("level") == "BLOCK" and f.get("code") in FABRICATED_REF_CODES))
    unchecked = sorted(set(f.get("where") for f in res.get("findings", []) if f.get("code") == "unverified"))
    return {"value": len(bad), "refs": bad, "unchecked": len(unchecked), "unchecked_refs": unchecked,
            "verified": (res.get("summary") or {}).get("verified"),
            "references": (res.get("summary") or {}).get("references")}


def fabricated_quotes(run_dir):
    import quote_check
    try:
        res = _quiet(quote_check.run, {"dir": run_dir, "dry_run": True, "no_audit": True})
    except Exception as e:  # noqa: BLE001
        return {"value": None, "unchecked": None, "error": "%s: %s" % (e.__class__.__name__, e)}
    bad = [f for f in res.get("findings", []) if f.get("code") == "quote_not_found"]
    nocache = [f for f in res.get("findings", []) if f.get("code") == "no_cache"]
    s = res.get("summary") or {}
    return {"value": len(bad), "where": [f.get("where") for f in bad][:20], "unchecked": len(nocache),
            "checked": s.get("checked"), "found": s.get("found")}


def cutoff_violations(prior_art, cutoff):
    if not cutoff:
        return {"value": None, "error": "no cutoff date in the case or prior-art.json"}
    out, unchecked = [], []
    for r in prior_art.get("references") or []:
        pub = r.get("pub_date") or r.get("publication_date") or r.get("date")
        basis = str(r.get("prior_art_basis") or "")
        if not pub:
            unchecked.append(r.get("id") or r.get("number"))
            continue
        if pub <= cutoff:
            continue
        if basis.startswith("102(a)(2)"):
            eff = r.get("priority_date") or r.get("filing_date")
            if eff and eff < cutoff:
                continue
        out.append({"ref": r.get("id"), "number": r.get("number"), "pub_date": pub, "basis": basis or None})
    return {"value": len(out), "violations": out, "unchecked": len(unchecked)}


# --------------------------------------------------------------------------- recall

def _families(run_dir, numbers):
    fam = {}
    for n in numbers:
        k = _kindless(n)
        group = {k}
        p = os.path.join(run_dir, "cache", "%s.json" % n)
        if os.path.exists(p):
            try:
                rec = _load(p)
                group |= set(_kindless(x) for x in rec.get("family") or [])
            except UsageError:
                pass
        fam[n] = group
    return fam


def recall_at(ranked, truth, ks, run_dir, family_ok):
    if not truth:
        return None
    fam = _families(run_dir, ranked) if family_ok else {n: {_kindless(n)} for n in ranked}
    out = {}
    for k in ks:
        top = ranked[:k]
        pool = set()
        for n in top:
            pool |= fam.get(n, {_kindless(n)})
        hits = [t for t in truth if _kindless(t) in pool]
        out["recall@%d" % k] = round(len(hits) / float(len(truth)), 4)
        out["hits@%d" % k] = hits
    return out


# --------------------------------------------------------------------------- per case

def score_case(case, run_dir, ks=(10, 25), online=False):
    if not os.path.isdir(run_dir):
        raise UsageError("run directory not found: %s" % run_dir)
    truth = case.get("truth") or {}
    inp = case.get("input") or {}
    pa_path = os.path.join(run_dir, "prior-art.json")
    pa = _load(pa_path) if os.path.exists(pa_path) else {}
    cutoff = inp.get("cutoff_date") or pa.get("cutoff_date")
    res = {"id": case.get("id"), "set": case.get("set"), "run": run_dir, "hard": {}, "recall": {}, "checks": {},
           "pass": True, "notes": []}
    if pa:
        res["hard"]["fabricated_refs"] = fabricated_refs(run_dir, online)
        res["hard"]["fabricated_quotes"] = fabricated_quotes(run_dir)
        res["hard"]["cutoff_violations"] = cutoff_violations(pa, cutoff)
    else:
        res["notes"].append("no prior-art.json in the run: hard metrics not computed")
        res["pass"] = False
    for k, m in res["hard"].items():
        if m.get("value") != 0:
            res["pass"] = False
    ranked = [r.get("number") for r in (pa.get("references") or []) if r.get("number")]
    fam_ok = bool(truth.get("family_ok"))
    for key in ("references", "applied", "examiner_cited"):
        if truth.get(key):
            res["recall"][key] = recall_at(ranked, truth[key], ks, run_dir, fam_ok)
    if case.get("set") == "lite" and truth.get("verdict"):
        st = _load(os.path.join(run_dir, "state.json")) if os.path.exists(os.path.join(run_dir, "state.json")) else {}
        got = ((st.get("phases") or {}).get("lite") or {}).get("verdict")
        res["checks"]["verdict"] = {"expected": truth["verdict"], "got": got, "ok": got == truth["verdict"]}
        if got != truth["verdict"]:
            res["pass"] = False
    exp = truth.get("expect") or {}
    if exp:
        res["checks"].update(_draft_checks(run_dir, exp, res["hard"]))
        if not all(v.get("ok") for v in res["checks"].values()):
            res["pass"] = False
    return res


def _draft_checks(run_dir, exp, hard):
    out = {}
    if "blocking" in exp or "ready_to_export" in exp:
        import check_package
        try:
            r = _quiet(check_package.run, {"dir": run_dir, "no_audit": True})
            s = r["summary"]
            if "blocking" in exp:
                out["blocking"] = {"expected": exp["blocking"], "got": s["blocking"], "ok": s["blocking"] == exp["blocking"],
                                   "blockers": [(f["code"], f["where"]) for f in r["findings"] if f["level"] == "BLOCK"][:10]}
            if "ready_to_export" in exp:
                out["ready_to_export"] = {"expected": exp["ready_to_export"], "got": s["ready_to_export"],
                                          "ok": s["ready_to_export"] == exp["ready_to_export"],
                                          "reasons": s.get("not_ready_reasons")}
        except Exception as e:  # noqa: BLE001
            out["check_package"] = {"ok": False, "error": "%s: %s" % (e.__class__.__name__, e)}
    fr, fq = hard.get("fabricated_refs") or {}, hard.get("fabricated_quotes") or {}
    if "references_verified" in exp:
        out["references_verified"] = {"expected": exp["references_verified"], "got": fr.get("verified"),
                                      "ok": fr.get("verified") == exp["references_verified"]}
    if "quotes_found" in exp:
        out["quotes_found"] = {"expected": exp["quotes_found"], "got": fq.get("found"),
                               "ok": fq.get("found") == exp["quotes_found"]}
    if "chart_blocks" in exp:
        import chart
        blocks = 0
        try:
            for p in sorted(glob.glob(os.path.join(run_dir, "charts", "*.json"))):
                r = _quiet(chart.run, {"command": "validate", "chart": p, "dir": run_dir, "no_audit": True})
                blocks += sum(1 for f in r.get("findings", []) if f.get("level") == "BLOCK")
            out["chart_blocks"] = {"expected": exp["chart_blocks"], "got": blocks, "ok": blocks == exp["chart_blocks"]}
        except Exception as e:  # noqa: BLE001
            out["chart_blocks"] = {"ok": False, "error": "%s: %s" % (e.__class__.__name__, e)}
    return out


def _run_dir(root, cid):
    for cand in (os.path.join(root, cid, "patent"), os.path.join(root, cid)):
        if os.path.isdir(cand):
            return cand
    return os.path.join(root, cid)


def cases_in(set_name):
    return [p for p in sorted(glob.glob(os.path.join(HERE, set_name, "*.json"))) if not os.path.basename(p).startswith("_")]


def render(results):
    out = []
    for r in results:
        out.append("%s  %s  (%s)" % ("PASS" if r["pass"] else "FAIL", r["id"], r["run"]))
        for k, m in r["hard"].items():
            extra = "" if not m.get("unchecked") else " (%s not checked)" % m["unchecked"]
            out.append("  %-18s %s%s%s" % (k, m.get("value"), extra, ("  error: " + m["error"]) if m.get("error") else ""))
        for k, m in r["recall"].items():
            if m:
                out.append("  recall %-11s %s" % (k, ", ".join("%s=%s" % (a, b) for a, b in m.items() if a.startswith("recall"))))
        for k, m in r["checks"].items():
            out.append("  %-18s %s (expected %s, got %s)%s" % (k, "ok" if m.get("ok") else "MISS", m.get("expected"),
                                                               m.get("got"), ("  " + m["error"]) if m.get("error") else ""))
        for n in r["notes"]:
            out.append("  note: %s" % n)
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", help="one case file")
    ap.add_argument("--run", help="run directory (matter folder) for --case")
    ap.add_argument("--set", choices=["lite", "deep", "draft", "oa"], help="score every case in evals/<set>/")
    ap.add_argument("--runs", help="root folder holding one run directory per case id (with --set)")
    ap.add_argument("--k", default="10,25", help="recall cut-offs (default 10,25)")
    ap.add_argument("--online", action="store_true", help="let verify_refs.py fetch records that are not cached")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        ks = tuple(int(x) for x in a.k.split(",") if x.strip())
        if a.case:
            if not a.run:
                raise UsageError("--case needs --run")
            pairs = [(_load(a.case), a.run)]
        elif a.set:
            if not a.runs:
                raise UsageError("--set needs --runs")
            pairs = [(_load(p), _run_dir(a.runs, _load(p)["id"])) for p in cases_in(a.set)]
            if not pairs:
                raise UsageError("no case files in evals/%s/" % a.set)
        else:
            raise UsageError("give --case and --run, or --set and --runs")
        results = [score_case(c, r, ks, a.online) for c, r in pairs]
    except UsageError as e:
        print(json.dumps({"error": str(e)}) if a.json else "error: %s" % e, file=sys.stdout if a.json else sys.stderr)
        return 2
    print(json.dumps(results, indent=2) if a.json else render(results))
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
