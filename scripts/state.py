#!/usr/bin/env python3
"""patentassist matter state: init / show / set / decide / hash / stale / log / bar.

State lives in <dir>/state.json (patentassist/state@1); see references/state-files.md.

Examples:
    python3 scripts/state.py init --title "Helmet signal system" --mode inventor --confidentiality abstracted
    python3 scripts/state.py show
    python3 scripts/state.py set phase lite
    python3 scripts/state.py set dates.earliest_public_disclosure '"2026-03-02"'
    python3 scripts/state.py set dates.disclosures_confirmed none   # asked: no disclosure, sale, offer, or use
    python3 scripts/state.py set open_questions "Inventor 2 address" --append
    python3 scripts/state.py decide --gate lite --choice "run deep search"
    python3 scripts/state.py hash draft/spec.md
    python3 scripts/state.py stale
    python3 scripts/state.py log --kind note --json-detail '{"text": "user confirmed no sales"}'
    python3 scripts/state.py bar

Gate ids for `decide` (canonical): clarify, scope, lite, deep, claims, package, oa-strategy, oa-final, mine.
A custom gate id needs --force-gate.

Bar clock: compute_bar reports `unknown` until the bar questions are answered, that is until
dates.disclosures_confirmed is "none" (asked; no public disclosure, sale, offer, or public use)
or a disclosure/sale/offer/use date is recorded. "yes" without a date stays `unknown`.

Staleness: draft/filing.json is hashed without its computed fields (total_fee, spec_pages,
drawing_sheets), so writing the fee or page counts back does not make draft/out/ stale.

This module also holds small helpers (JSON I/O, audit, findings output) that the
other search-phase scripts import.

Exit codes: 0 ok, 1 blocking findings (stale artifacts), 2 usage/input error.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _dates import add_months, holiday_name, is_weekend, parse_date, roll_forward  # noqa: E402

SCHEMA_STATE = "patentassist/state@1"
SCHEMA_PRIOR_ART = "patentassist/prior-art@1"
SCHEMA_PATENT = "patentassist/patent@1"
SCHEMA_CHART = "patentassist/chart@1"

AUDIT_KINDS = ("query", "fetch", "verify", "quote", "gate", "check", "export", "note")
GATES = ("clarify", "scope", "lite", "deep", "claims", "package", "oa-strategy", "oa-final", "mine")
DISCLOSURES_CONFIRMED = (None, "none", "yes")
# filing.json fields that scripts compute and write back; excluded from staleness hashes
FILING_COMPUTED_FIELDS = ("total_fee", "spec_pages", "drawing_sheets")


# --------------------------------------------------------------------------- helpers


class UsageError(Exception):
    """Bad input or arguments (exit 2)."""


class SourceError(Exception):
    """Network or source failure (exit 3)."""


def utc_now():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso(override=None):
    if override:
        return parse_date(override).isoformat()
    return _dt.date.today().isoformat()


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def check_schema(obj, expected, path="file"):
    """Refuse a file whose schema family or major version we do not know."""
    if not isinstance(obj, dict):
        raise UsageError("%s: not a JSON object" % path)
    got = obj.get("schema")
    if not isinstance(got, str) or "@" not in got:
        raise UsageError("%s: missing schema string (expected %s)" % (path, expected))
    fam, ver = got.split("@", 1)
    efam, ever = expected.split("@", 1)
    if fam != efam or ver.split(".")[0] != ever.split(".")[0]:
        raise UsageError("%s: schema %s is not supported (expected %s)" % (path, got, expected))
    return obj


def to_namespace(args, defaults):
    """Let run() accept a dict (host-app tool call) or an argparse Namespace."""
    if isinstance(args, argparse.Namespace):
        merged = dict(defaults)
        merged.update({k: v for k, v in vars(args).items()})
        return argparse.Namespace(**merged)
    merged = dict(defaults)
    merged.update(args or {})
    return argparse.Namespace(**merged)


def current_phase(dirpath):
    try:
        return read_json(os.path.join(dirpath, "state.json")).get("phase")
    except Exception:
        return None


def audit(dirpath, kind, no_audit=False, **fields):
    """Append one line to <dir>/audit.jsonl. Never rewrites the file."""
    if no_audit:
        return None
    if kind not in AUDIT_KINDS:
        raise UsageError("unknown audit kind %r (allowed: %s)" % (kind, ", ".join(AUDIT_KINDS)))
    rec = {"ts": utc_now(), "kind": kind}
    for k, v in fields.items():
        if v is not None:
            rec[k] = v
    if "phase" not in rec:
        ph = current_phase(dirpath)
        if ph:
            rec["phase"] = ph
    os.makedirs(dirpath, exist_ok=True)
    with open(os.path.join(dirpath, "audit.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def finding(level, code, where, message):
    return {"level": level, "code": code, "where": where, "message": message}


def new_result():
    return {"ok": True, "exit_code": 0, "findings": [], "checks_run": [], "checks_skipped": [],
            "summary": {}, "text": []}


def finalize(result):
    blocks = [f for f in result["findings"] if f["level"] == "BLOCK"]
    warns = [f for f in result["findings"] if f["level"] == "WARN"]
    result["summary"].setdefault("blocking", len(blocks))
    result["summary"].setdefault("warnings", len(warns))
    if blocks and result.get("exit_code", 0) == 0:
        result["exit_code"] = 1
    result["ok"] = result.get("exit_code", 0) == 0
    return result


def emit(result, as_json=False, stream=None):
    stream = stream or sys.stdout
    if as_json:
        out = {k: v for k, v in result.items() if k != "text"}
        stream.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
        return
    for line in result.get("text", []):
        stream.write(line + "\n")
    for f in result.get("findings", []):
        stream.write("%-5s  %s  %s  %s\n" % (f["level"], f["code"], f["where"], f["message"]))
    if result.get("checks_run") or result.get("checks_skipped"):
        if result.get("checks_run"):
            stream.write("Checks run: %s\n" % ", ".join(result["checks_run"]))
        for s in result.get("checks_skipped", []):
            stream.write("Check skipped: %s (%s)\n" % (s["check"], s["reason"]))
    if result.get("error"):
        stream.write("ERROR: %s\n" % result["error"])


def add_common(p, sub=False, network=False):
    """Common options. On subparsers they use SUPPRESS so the main parser value wins
    unless the option is given after the subcommand."""
    d = (lambda v: argparse.SUPPRESS) if sub else (lambda v: v)
    p.add_argument("--dir", default=d("patent"), help="matter folder (default: patent)")
    p.add_argument("--json", action="store_true", default=d(False), help="machine-readable output")
    p.add_argument("--no-audit", action="store_true", default=d(False), help="do not append to audit.jsonl")
    if network:
        p.add_argument("--offline", action="store_true", default=d(False), help="use cache only, no network")


def cli_main(build_parser, run, argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", "x") is None:
        parser.print_help()
        return 2
    try:
        res = run(args)
    except UsageError as e:
        res = new_result()
        res.update({"ok": False, "exit_code": 2, "error": str(e)})
    except SourceError as e:
        res = new_result()
        res.update({"ok": False, "exit_code": 3, "error": str(e)})
    emit(res, getattr(args, "json", False))
    return int(res.get("exit_code", 0))


def sha256_path(path):
    """sha256 of a file; for a directory, of its sorted relative paths + file hashes."""
    if os.path.isdir(path):
        h = hashlib.sha256()
        for root, dirs, files in os.walk(path):
            dirs.sort()
            for name in sorted(files):
                fp = os.path.join(root, name)
                rel = os.path.relpath(fp, path).replace(os.sep, "/")
                h.update(rel.encode("utf-8") + b"\0")
                h.update(sha256_path(fp).encode("ascii") + b"\n")
        return h.hexdigest()
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_prior_art(dirpath, required=True):
    path = os.path.join(dirpath, "prior-art.json")
    if not os.path.exists(path):
        if required:
            raise UsageError("%s not found (run state.py init first)" % path)
        return None
    return check_schema(read_json(path), SCHEMA_PRIOR_ART, path)


def save_prior_art(dirpath, obj):
    write_json(os.path.join(dirpath, "prior-art.json"), obj)


def empty_prior_art():
    return {
        "schema": SCHEMA_PRIOR_ART,
        "purpose": None,
        "stage": None,
        "cutoff_date": None,
        "cutoff_basis": None,
        "elements": [],
        "queries": [],
        "references": [],
        "read_not_cited": [],
        "combinations": [],
        "not_searched": [],
        "vocabulary": {},
    }


# --------------------------------------------------------------------------- bar


DISCLOSURE_KEYS = ("earliest_public_disclosure", "earliest_sale_or_offer", "earliest_public_use")
_DISCLOSURE_LABEL = {
    "earliest_public_disclosure": "public disclosure",
    "earliest_sale_or_offer": "sale or offer for sale",
    "earliest_public_use": "public use",
}


def _d(v):
    if v in (None, ""):
        return None
    try:
        return parse_date(v)
    except ValueError:
        return None


def compute_bar(dates, today=None):
    """US 1-year grace (35 USC 102(b)(1)) and a coarse foreign absolute-novelty read.

    Returns {us_status, us_last_day, foreign_status, computed, trigger, days_left, notes}.
    us_last_day = earliest disclosure/sale/offer/use + 12 months, rolled forward past
    weekends and DC federal holidays (35 USC 21(b)). This is a screening aid, not a
    legal opinion: it only knows the dates the user gave."""
    dates = dates or {}
    today_d = parse_date(today) if today else _dt.date.today()
    res = {"us_status": "clear", "us_last_day": None, "foreign_status": "intact",
           "computed": today_d.isoformat(), "trigger": None, "days_left": None, "notes": []}
    confirmed = dates.get("disclosures_confirmed")
    bad = [k for k in DISCLOSURE_KEYS + ("provisional_filed", "nonprovisional_filed")
           if dates.get(k) not in (None, "") and _d(dates.get(k)) is None]
    if bad:
        res.update({"us_status": "unknown", "foreign_status": "unknown"})
        res["notes"].append("unreadable date(s): %s" % ", ".join(bad))
        return res
    triggers = sorted(((k, _d(dates.get(k))) for k in DISCLOSURE_KEYS if _d(dates.get(k))),
                      key=lambda kv: kv[1])
    filings = [x for x in (_d(dates.get("provisional_filed")), _d(dates.get("nonprovisional_filed"))) if x]
    filed = min(filings) if filings else None

    if not triggers:
        if confirmed == "none":
            res["notes"].append("User confirmed no public disclosure, sale, offer, or public use. "
                                "File before any disclosure to keep foreign rights.")
            return res
        res.update({"us_status": "unknown", "foreign_status": "unknown"})
        if confirmed == "yes":
            res["notes"].append("User reported a public disclosure, sale, offer, or public use, but no date is "
                                "recorded: set dates.earliest_public_disclosure / earliest_sale_or_offer / "
                                "earliest_public_use.")
        else:
            res["notes"].append("Bar questions not answered yet: ask about any public disclosure, sale or offer for "
                                "sale, and public use, then record the dates or set dates.disclosures_confirmed none.")
        return res
    if confirmed == "none":
        res["notes"].append("dates.disclosures_confirmed is 'none' but a disclosure/sale/use date is recorded; "
                            "the recorded date is used. Re-ask the user and correct one of them.")

    key, tdate = triggers[0]
    res["trigger"] = {"field": key, "date": tdate.isoformat(), "what": _DISCLOSURE_LABEL[key]}
    raw_last = add_months(tdate, 12)
    last = roll_forward(raw_last)
    res["us_last_day"] = last.isoformat()
    if last != raw_last:
        why = holiday_name(raw_last) or ("Saturday" if raw_last.weekday() == 5 else
                                        "Sunday" if raw_last.weekday() == 6 else "closed day")
        res["notes"].append("One year after %s is %s (%s); rolled forward to %s under 35 USC 21(b)."
                            % (tdate.isoformat(), raw_last.isoformat(), why, last.isoformat()))

    if filed:
        if filed < tdate:
            res["us_status"] = "clear"
            res["notes"].append("Filed %s, before the earliest %s. This holds only for subject matter the filing "
                                "describes; a later-disclosed variant it does not describe has its own clock from "
                                "the disclosure." % (filed.isoformat(), _DISCLOSURE_LABEL[key]))
        elif filed <= last:
            res["us_status"] = "clear"
            res["notes"].append("Filed %s, inside the 1-year grace period (35 USC 102(b)(1)); "
                                "the filing must support what is claimed." % filed.isoformat())
        else:
            res["us_status"] = "likely_barred"
            res["notes"].append("Earliest filing %s is after the grace period ended %s."
                                % (filed.isoformat(), last.isoformat()))
    else:
        left = (last - today_d).days
        res["days_left"] = left
        if left >= 0:
            res["us_status"] = "clock_running"
            res["notes"].append("US grace period: file on or before %s (%d days left)." % (last.isoformat(), left))
        else:
            res["us_status"] = "likely_barred"
            res["notes"].append("US grace period ended %s (%d days ago)." % (last.isoformat(), -left))
    res["notes"].append("The 102(b)(1) exception covers the inventor's own disclosure (or one derived from "
                        "the inventor); it does not cover an independent third-party disclosure.")

    before_filing = [(k, d) for k, d in triggers if not filed or d <= filed]
    if not before_filing:
        res["foreign_status"] = "intact"
    elif any(k in ("earliest_public_disclosure", "earliest_public_use") for k, _ in before_filing):
        res["foreign_status"] = "likely_lost"
        res["notes"].append("Most foreign offices (EPO, CN) require absolute novelty: a public disclosure or "
                            "public use before filing likely ends patent rights there. JP and KR have a 12-month "
                            "grace period with formal requirements; check before relying on it.")
    else:
        res["foreign_status"] = "at_risk"
        res["notes"].append("A sale or offer before filing may or may not be a public disclosure abroad "
                            "(a confidential offer often is not). Treat foreign rights as at risk.")
    return res


# --------------------------------------------------------------------------- state schema


ENUMS = {
    "profile.mode": ["inventor", "practitioner"],
    "profile.role": ["inventor", "attorney", "agent", "paralegal", "other"],
    "profile.confidentiality": ["abstracted", "detailed"],
    "phase": ["setup", "clarify", "lite", "deep", "draft", "filed", "prosecution"],
    "phases.clarify.status": ["not_started", "in_progress", "done", "skipped"],
    "phases.lite.status": ["not_started", "in_progress", "done", "skipped"],
    "phases.deep.status": ["not_started", "in_progress", "done", "skipped"],
    "phases.draft.status": ["not_started", "in_progress", "done", "skipped"],
    "phases.lite.verdict": ["knocked_out", "crowded", "no_knockout", None],
    "phases.deep.purpose": ["patentability", "fto", "invalidity", "landscape", None],
    "phases.draft.filing_type": ["provisional", "nonprovisional", "nonprovisional_claiming_priority", None],
    "dates.disclosures_confirmed": list(DISCLOSURES_CONFIRMED),
}
DATE_PATHS = {
    "dates.conception", "dates.earliest_public_disclosure", "dates.earliest_sale_or_offer",
    "dates.earliest_public_use", "dates.provisional_filed", "dates.nonprovisional_filed",
    "dates.target_filing", "phases.clarify.date", "phases.lite.date", "phases.deep.date", "phases.draft.date",
}
STRING_PATHS = {
    "matter.title": False,  # value: nullable?
    "profile.reg_no": True, "profile.customer_no": True, "dates.provisional_app_no": True,
    "phases.clarify.report": True, "phases.lite.report": True, "phases.deep.report": True, "phases.deep.outlook": True,
}
BOOL_PATHS = {"profile.keys.uspto_odp", "profile.keys.epo_ops", "profile.keys.lens",
              "phases.draft.claims_locked", "phases.draft.figures_locked"}
COMPUTED_PREFIXES = ("bar", "artifacts", "decisions", "schema", "matter.updated", "matter.created")


def default_state(title, mode="inventor", role=None, today=None, confidentiality="abstracted"):
    t = today_iso(today)
    return {
        "schema": SCHEMA_STATE,
        "matter": {"title": title, "created": t, "updated": utc_now()},
        "profile": {
            "mode": mode,
            "role": role or ("inventor" if mode == "inventor" else "attorney"),
            "reg_no": None,
            "customer_no": None,
            "confidentiality": confidentiality or "abstracted",
            "keys": {
                "uspto_odp": bool(os.environ.get("USPTO_ODP_API_KEY")),
                "epo_ops": bool(os.environ.get("EPO_OPS_KEY") and os.environ.get("EPO_OPS_SECRET")),
                "lens": bool(os.environ.get("LENS_TOKEN")),
            },
        },
        "phase": "setup",
        "phases": {
            "clarify": {"status": "not_started", "date": None, "report": None},
            "lite": {"status": "not_started", "verdict": None, "date": None, "report": None},
            "deep": {"status": "not_started", "purpose": None, "outlook": None, "date": None, "report": None},
            "draft": {"status": "not_started", "filing_type": None, "claims_locked": False,
                      "figures_locked": False, "date": None},
        },
        "dates": {
            "conception": None, "earliest_public_disclosure": None, "earliest_sale_or_offer": None,
            "earliest_public_use": None, "provisional_filed": None, "provisional_app_no": None,
            "nonprovisional_filed": None, "target_filing": None, "disclosures_confirmed": None,
        },
        "bar": {"us_status": "unknown", "us_last_day": None, "foreign_status": "unknown", "computed": None},
        "artifacts": {},
        "depends": {
            "draft/claims.md": ["invention-disclosure.md", "prior-art.json"],
            "draft/spec.md": ["draft/claims.md", "draft/figures.json"],
            "draft/out/": ["draft/spec.md", "draft/claims.md", "draft/figures.json", "draft/filing.json"],
        },
        "decisions": [],
        "open_questions": [],
    }


def state_path(dirpath):
    return os.path.join(dirpath, "state.json")


def load_state(dirpath):
    p = state_path(dirpath)
    if not os.path.exists(p):
        raise UsageError("%s not found (run: state.py init --title ...)" % p)
    return check_schema(read_json(p), SCHEMA_STATE, p)


def save_state(dirpath, st):
    st.setdefault("matter", {})["updated"] = utc_now()
    write_json(state_path(dirpath), st)


def _leaf_paths():
    return set(ENUMS) | DATE_PATHS | set(STRING_PATHS) | BOOL_PATHS | {"open_questions"}


def validate_value(path, value):
    """Return the (possibly normalized) value or raise UsageError."""
    for pre in COMPUTED_PREFIXES:
        if path == pre or path.startswith(pre + "."):
            raise UsageError("%s is computed or append-only; use the dedicated command "
                             "(bar is recomputed from dates; decide; hash)" % path)
    if path.startswith("depends."):
        if not (isinstance(value, list) and all(isinstance(x, str) and x for x in value)):
            raise UsageError("%s must be a JSON list of relative paths" % path)
        return value
    if path == "depends":
        if not isinstance(value, dict):
            raise UsageError("depends must be an object {downstream: [inputs]}")
        for k, v in value.items():
            validate_value("depends." + k, v)
        return value
    if path in ENUMS:
        if value not in ENUMS[path]:
            raise UsageError("%s must be one of %s (got %r)" % (
                path, ", ".join("null" if x is None else x for x in ENUMS[path]), value))
        return value
    if path in DATE_PATHS:
        if value is None:
            return None
        try:
            return parse_date(value).isoformat() if isinstance(value, str) and re.match(
                r"^\d{4}-\d{2}-\d{2}$", value.strip()) else _bad_date(path, value)
        except ValueError:
            return _bad_date(path, value)
    if path in STRING_PATHS:
        if value is None and STRING_PATHS[path]:
            return None
        if not isinstance(value, str) or not value.strip():
            raise UsageError("%s must be a non-empty string" % path)
        return value
    if path in BOOL_PATHS:
        if not isinstance(value, bool):
            raise UsageError("%s must be true or false" % path)
        return value
    if path == "open_questions":
        if not (isinstance(value, list) and all(isinstance(x, str) for x in value)):
            raise UsageError("open_questions must be a JSON list of strings")
        return value
    children = sorted(p for p in _leaf_paths() if p.startswith(path + "."))
    if children and isinstance(value, dict):
        out = {}
        for k, v in value.items():
            out[k] = validate_value(path + "." + k, v)
        return out
    raise UsageError("unknown path %r. Settable: %s, depends.<file>" % (path, ", ".join(sorted(_leaf_paths()))))


def _bad_date(path, value):
    raise UsageError("%s must be an ISO date YYYY-MM-DD or null (got %r)" % (path, value))


def _set_path(obj, path, value, merge=False):
    if path.startswith("depends."):
        obj.setdefault("depends", {})[path[len("depends."):]] = value
        return
    parts = path.split(".")
    cur = obj
    for p in parts[:-1]:
        if not isinstance(cur.get(p), dict):
            cur[p] = {}
        cur = cur[p]
    if merge and isinstance(value, dict) and isinstance(cur.get(parts[-1]), dict):
        cur[parts[-1]].update(value)
    else:
        cur[parts[-1]] = value


def parse_cli_value(raw):
    """JSON if it parses, else the raw string (so `set phase lite` works)."""
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


# --------------------------------------------------------------------------- next gate


def next_gate(st):
    ph = st.get("phase")
    phases = st.get("phases", {})
    lite, deep, draft = phases.get("lite", {}), phases.get("deep", {}), phases.get("draft", {})
    bar = st.get("bar", {})
    dates = st.get("dates") or {}
    if dates.get("disclosures_confirmed") is None:
        if any(dates.get(k) for k in DISCLOSURE_KEYS):
            return ("Confirm the statutory-bar answers: is each recorded disclosure/sale/offer/use date the earliest, "
                    "and was there any other? Then `state.py set dates.disclosures_confirmed yes`.")
        return ("Ask the statutory-bar questions (earliest public disclosure, sale/offer, public use) and record them "
                "with `state.py set dates.*`; if there were none, `state.py set dates.disclosures_confirmed none`.")
    if bar.get("us_status") == "unknown":
        return "Ask the statutory-bar questions (earliest public disclosure, sale/offer, public use) and record them with `state.py set dates.*`."
    if ph in ("setup", "clarify"):
        return "Clarify the actual invention in invention-disclosure.md; confirm scope and record a Phase 0 review before searching."
    if ph == "lite" or lite.get("status") in ("not_started", "in_progress"):
        if lite.get("status") != "done":
            return "Finish the lite search, run verify_refs.py and quote_check.py, then show the lite gate."
    if lite.get("status") == "done" and deep.get("status") == "not_started" and ph in ("lite", "setup"):
        v = lite.get("verdict")
        if v == "knocked_out":
            return "Gate lite->deep: knocked out. Ask: stop, pivot the idea, or run the deep search anyway?"
        return "Gate lite->deep: %s. Ask: run the deep search (optional keys), or go straight to drafting?" % (v or "verdict not set")
    if deep.get("status") == "in_progress" or (ph == "deep" and deep.get("status") not in ("done", "skipped")):
        return "Finish the deep search (search_log.py coverage, verify_refs.py, quote_check.py), then show the deep->draft gate."
    if ph in ("deep", "lite") and deep.get("status") in ("done", "skipped") and draft.get("status") == "not_started":
        return "Gate deep->draft: ask provisional vs nonprovisional, then confirm the current claim-scope checkpoint."
    if ph == "draft" and draft.get("status") == "done":
        return ("Package exported: walk the Patent Center filing steps (the human files and pays), then record "
                "dates.provisional_filed or dates.nonprovisional_filed and docket the deadlines.")
    if ph == "draft" or draft.get("status") == "in_progress":
        if not draft.get("claims_locked"):
            return "Draft and review claims (check_claims.py); confirm their current scope and figure plan."
        if not draft.get("figures_locked"):
            return "Confirm the current figure plan (figures.json), then develop the specification."
        return "Record a current draft assessment with review.py; run state.py stale and check_package.py before export."
    if ph == "filed":
        return "Docket deadlines (deadlines.py): 12-month provisional clock, IDS duty, foreign filing."
    if ph == "prosecution":
        return "Parse the office action (oa_parse.py) and plan the response."
    return "Review state and pick the next phase."


# --------------------------------------------------------------------------- commands


def cmd_init(a, res):
    dirpath = a.dir
    if os.path.exists(state_path(dirpath)) and not a.force:
        raise UsageError("%s already exists (use --force to re-create state.json)" % state_path(dirpath))
    if a.mode not in ENUMS["profile.mode"]:
        raise UsageError("--mode must be inventor or practitioner")
    if a.role is not None and a.role not in ENUMS["profile.role"]:
        raise UsageError("--role must be one of %s" % ", ".join(ENUMS["profile.role"]))
    conf = a.confidentiality or "abstracted"
    if conf not in ENUMS["profile.confidentiality"]:
        raise UsageError("--confidentiality must be abstracted or detailed")
    if not a.title or not a.title.strip():
        raise UsageError("--title is required")
    for sub in ("cache", "charts", "reports", "draft", "draft/out", "prosecution"):
        os.makedirs(os.path.join(dirpath, sub), exist_ok=True)
    st = default_state(a.title.strip(), a.mode, a.role, a.today, conf)
    save_state(dirpath, st)
    pa = os.path.join(dirpath, "prior-art.json")
    created_pa = False
    if not os.path.exists(pa):
        save_prior_art(dirpath, empty_prior_art())
        created_pa = True
    audit(dirpath, "note", a.no_audit, action="init", title=st["matter"]["title"], mode=a.mode, confidentiality=conf)
    res["state"] = st
    res["text"].append("Initialized %s (mode %s, role %s, confidentiality %s)." % (
        dirpath, st["profile"]["mode"], st["profile"]["role"], conf))
    if a.confidentiality is None:
        res["text"].append("Confidentiality defaulted to abstracted (generic terms only in web queries); "
                           "pass --confidentiality detailed if the user allowed specific technical terms.")
    res["text"].append("prior-art.json %s." % ("created" if created_pa else "kept (already existed)"))
    if a.role is None and a.mode == "practitioner":
        res["text"].append("Role defaulted to attorney; change with: state.py set profile.role agent")
    res["text"].append("Next: " + next_gate(st))


def cmd_show(a, res):
    st = load_state(a.dir)
    if st.get("bar", {}).get("computed"):
        st["bar"] = compute_bar(st.get("dates"), a.today)
    m = st.get("matter", {})
    p = st.get("profile", {})
    lines = res["text"]
    lines.append("Matter: %s (created %s)" % (m.get("title"), m.get("created")))
    lines.append("Mode: %s  role: %s  confidentiality: %s  keys: %s" % (
        p.get("mode"), p.get("role"), p.get("confidentiality"),
        ", ".join(k for k, v in (p.get("keys") or {}).items() if v) or "none"))
    lines.append("Phase: %s" % st.get("phase"))
    for name in ("clarify", "lite", "deep", "draft"):
        ph = st.get("phases", {}).get(name, {})
        extras = ["%s=%s" % (k, v) for k, v in ph.items() if k != "status" and v not in (None, False, "")]
        lines.append("  %-5s %-11s %s" % (name, ph.get("status"), "  ".join(extras)))
    b = st.get("bar", {})
    bar_line = "Bar: US %s" % b.get("us_status")
    if b.get("us_last_day"):
        bar_line += " (last day %s)" % b["us_last_day"]
    bar_line += "; foreign %s" % b.get("foreign_status")
    if b.get("computed"):
        bar_line += "  [computed %s]" % b["computed"]
    lines.append(bar_line)
    for n in b.get("notes", []) or []:
        lines.append("  - " + n)
    dates = {k: v for k, v in (st.get("dates") or {}).items() if v}
    lines.append("Dates: " + (", ".join("%s=%s" % kv for kv in dates.items()) or "none recorded"))
    oq = st.get("open_questions") or []
    lines.append("Open questions (%d):" % len(oq))
    for q in oq:
        lines.append("  - " + q)
    dec = st.get("decisions") or []
    lines.append("Decisions (%d)%s" % (len(dec), ":" if dec else ""))
    for d in dec[-5:]:
        lines.append("  %s  %s: %s%s" % (d.get("date"), d.get("gate"), d.get("choice"),
                                          ("  (%s)" % d["note"]) if d.get("note") else ""))
    pa = load_prior_art(a.dir, required=False)
    if pa:
        refs = pa.get("references", [])
        ver = sum(1 for r in refs if r.get("verified"))
        lines.append("Prior art: %d references (%d verified), %d queries, cutoff %s" % (
            len(refs), ver, len(pa.get("queries", [])), pa.get("cutoff_date")))
    stale = compute_stale(a.dir, st)
    if stale:
        lines.append("Stale: %s" % ", ".join(s["downstream"] for s in stale))
    gate = next_gate(st)
    lines.append("Next: " + gate)
    res["state"] = st
    res["next_gate"] = gate
    res["stale"] = stale


def cmd_set(a, res):
    st = load_state(a.dir)
    path = a.path.strip()
    value = parse_cli_value(a.value)
    if a.append:
        if path != "open_questions" and not path.startswith("depends."):
            raise UsageError("--append works only for open_questions and depends.<file>")
        cur = list(st.get("open_questions") or []) if path == "open_questions" else \
            list((st.get("depends") or {}).get(path[len("depends."):], []))
        items = value if isinstance(value, list) else [value]
        for it in items:
            if it not in cur:
                cur.append(it)
        value = cur
    value = validate_value(path, value)
    _set_path(st, path, value, merge=isinstance(value, dict) and path not in ("depends",))
    if path == "dates" or path.startswith("dates."):
        st["bar"] = compute_bar(st.get("dates"), a.today)
        res["bar"] = st["bar"]
        res["text"].append("Bar recomputed: US %s%s; foreign %s" % (
            st["bar"]["us_status"],
            (" (last day %s)" % st["bar"]["us_last_day"]) if st["bar"]["us_last_day"] else "",
            st["bar"]["foreign_status"]))
    save_state(a.dir, st)
    audit(a.dir, "note", a.no_audit, action="set", path=path, value=value)
    res["text"].insert(0, "Set %s = %s" % (path, json.dumps(value, ensure_ascii=False)))
    res["value"] = value


def cmd_decide(a, res):
    st = load_state(a.dir)
    if not a.gate.strip() or not a.choice.strip():
        raise UsageError("--gate and --choice must be non-empty")
    if a.gate.strip() not in GATES and not a.force_gate:
        g = a.gate.strip().lower()
        hint = next((x for x in GATES if g.startswith(x)), None)
        raise UsageError("--gate %r is not a canonical gate id (%s)%s; pass --force-gate for a custom gate"
                         % (a.gate, ", ".join(GATES), ("; did you mean %r?" % hint) if hint else ""))
    rec = {"date": today_iso(a.today), "gate": a.gate.strip(), "choice": a.choice.strip(), "by": a.by}
    if a.note:
        rec["note"] = a.note
    st.setdefault("decisions", []).append(rec)
    save_state(a.dir, st)
    audit(a.dir, "gate", a.no_audit, gate=rec["gate"], choice=rec["choice"], note=a.note, by=a.by)
    res["decision"] = rec
    res["text"].append("Recorded decision at %s: %s" % (rec["gate"], rec["choice"]))


KNOWN_ARTIFACTS = ("invention-disclosure.md", "prior-art.json", "draft/claims.md", "draft/spec.md",
                   "draft/figures.json", "draft/filing.json")


def _all_tracked(st):
    paths = list(KNOWN_ARTIFACTS)
    for down, ins in (st.get("depends") or {}).items():
        for p in [down] + list(ins):
            if p not in paths:
                paths.append(p)
    return paths


def _norm_rel(p):
    return p.replace("\\", "/")


def _hash_rel(dirpath, rel):
    full = os.path.join(dirpath, rel)
    if not os.path.exists(full):
        return None
    if _norm_rel(os.path.normpath(rel)) == "draft/filing.json" and os.path.isfile(full):
        return sha256_filing(full)
    return sha256_path(full)


def _hash_matches(dirpath, rel, stored, cur):
    """True when the stored hash matches the current one. filing.json hashed before computed fields
    were excluded stored the raw-bytes hash; accept that too while the file is byte-identical."""
    if stored == cur:
        return True
    if stored and _norm_rel(os.path.normpath(rel)) == "draft/filing.json":
        full = os.path.join(dirpath, rel)
        return os.path.isfile(full) and sha256_path(full) == stored
    return False


def sha256_filing(path):
    """sha256 of filing.json without its computed fields (FILING_COMPUTED_FIELDS), canonicalized
    (sorted keys, compact separators), so writing total_fee / page counts back does not make
    draft/out/ stale. Falls back to the raw bytes when the file is not a JSON object."""
    try:
        obj = read_json(path)
    except (OSError, ValueError):
        return sha256_path(path)
    if not isinstance(obj, dict):
        return sha256_path(path)
    canon = {k: v for k, v in obj.items() if k not in FILING_COMPUTED_FIELDS}
    blob = json.dumps(canon, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def cmd_hash(a, res):
    st = load_state(a.dir)
    targets = [_norm_rel(p) for p in a.paths] if a.paths else _all_tracked(st)
    arts = st.setdefault("artifacts", {})
    depends = st.get("depends") or {}
    done, missing = [], []
    for rel in targets:
        h = _hash_rel(a.dir, rel)
        if h is None:
            missing.append(rel)
            continue
        entry = {"sha256": h, "updated": utc_now()}
        if rel in depends:
            snap = {}
            for inp in depends[rel]:
                ih = _hash_rel(a.dir, inp)
                if ih is not None:
                    snap[inp] = ih
            entry["inputs"] = snap
        arts[rel] = entry
        done.append(rel)
    save_state(a.dir, st)
    res["hashed"] = done
    res["missing"] = missing
    for rel in done:
        res["text"].append("hashed  %s  %s" % (arts[rel]["sha256"][:12], rel))
    if a.paths:
        for rel in missing:
            res["findings"].append(finding("WARN", "missing", rel, "file not found; not hashed"))


def _built(dirpath, rel):
    """A downstream artifact counts as built if the file exists, or the folder holds any file."""
    full = os.path.join(dirpath, rel)
    if os.path.isdir(full):
        return any(files for _, _, files in os.walk(full))
    return os.path.exists(full)


def compute_stale(dirpath, st):
    """List of {downstream, changed_inputs, reason} for downstream files whose inputs changed."""
    arts = st.get("artifacts") or {}
    depends = st.get("depends") or {}
    stale = {}

    def mtime(rel):
        full = os.path.join(dirpath, rel)
        if os.path.isdir(full):
            ts = [os.path.getmtime(os.path.join(r, f)) for r, _, fs in os.walk(full) for f in fs]
            return max(ts) if ts else None
        return os.path.getmtime(full) if os.path.exists(full) else None

    for down, inputs in depends.items():
        if not _built(dirpath, down):
            continue  # not built yet
        entry = arts.get(down) or {}
        snap = entry.get("inputs")
        changed = []
        reason = None
        if snap is not None:
            for inp in inputs:
                cur = _hash_rel(dirpath, inp)
                if cur is None:
                    continue
                if inp not in snap:
                    changed.append(inp)
                elif not _hash_matches(dirpath, inp, snap[inp], cur):
                    changed.append(inp)
            reason = "input hash changed since %s was hashed" % down
        else:
            dm = mtime(down)
            for inp in inputs:
                im = mtime(inp)
                if im is not None and dm is not None and im > dm + 1e-6:
                    rec = arts.get(inp)
                    if rec is None or not _hash_matches(dirpath, inp, rec.get("sha256"), _hash_rel(dirpath, inp)):
                        changed.append(inp)
            reason = "input newer than %s (never hashed with inputs; run state.py hash %s after rebuilding)" % (down, down)
        if changed:
            stale[down] = {"downstream": down, "changed_inputs": changed, "reason": reason}

    # propagate: a downstream whose input is itself stale is stale too
    grew = True
    while grew:
        grew = False
        for down, inputs in depends.items():
            if down in stale or not _built(dirpath, down):
                continue
            via = [i for i in inputs if i in stale]
            if via:
                stale[down] = {"downstream": down, "changed_inputs": via,
                               "reason": "depends on stale %s" % ", ".join(via)}
                grew = True
    return [stale[k] for k in depends if k in stale]


def cmd_stale(a, res):
    st = load_state(a.dir)
    res["checks_run"].append("stale")
    items = compute_stale(a.dir, st)
    res["stale"] = items
    for s in items:
        res["findings"].append(finding("BLOCK", "stale", s["downstream"],
                                       "rebuild: %s (%s)" % (", ".join(s["changed_inputs"]), s["reason"])))
    if not items:
        res["text"].append("No stale artifacts.")
    res["summary"]["stale"] = len(items)


def cmd_log(a, res):
    if a.kind not in AUDIT_KINDS:
        raise UsageError("--kind must be one of %s" % ", ".join(AUDIT_KINDS))
    detail = {}
    if a.json_detail:
        try:
            detail = json.loads(a.json_detail)
        except ValueError as e:
            raise UsageError("--json-detail is not valid JSON: %s" % e)
        if not isinstance(detail, dict):
            raise UsageError("--json-detail must be a JSON object")
    detail.pop("ts", None)
    detail.pop("kind", None)
    rec = audit(a.dir, a.kind, False, **detail)
    res["record"] = rec
    res["text"].append("logged %s" % a.kind)


def cmd_bar(a, res):
    st = load_state(a.dir)
    st["bar"] = compute_bar(st.get("dates"), a.today)
    save_state(a.dir, st)
    b = st["bar"]
    res["bar"] = b
    res["text"].append("US: %s%s; foreign: %s" % (
        b["us_status"], (" (last day %s)" % b["us_last_day"]) if b["us_last_day"] else "", b["foreign_status"]))
    for n in b["notes"]:
        res["text"].append("  - " + n)


COMMANDS = {"init": cmd_init, "show": cmd_show, "set": cmd_set, "decide": cmd_decide,
            "hash": cmd_hash, "stale": cmd_stale, "log": cmd_log, "bar": cmd_bar}

DEFAULTS = {"dir": "patent", "json": False, "no_audit": False, "today": None, "command": None,
            "title": None, "mode": "inventor", "role": None, "force": False, "path": None,
            "value": None, "append": False, "gate": None, "choice": None, "note": None, "by": "user",
            "paths": [], "kind": None, "json_detail": None, "confidentiality": None, "force_gate": False}


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.command not in COMMANDS:
        raise UsageError("command must be one of %s" % ", ".join(COMMANDS))
    res = new_result()
    res["command"] = a.command
    COMMANDS[a.command](a, res)
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="state.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(p)
    p.add_argument("--today", default=None, help=argparse.SUPPRESS)
    sp = p.add_subparsers(dest="command")

    def _sub(sub):
        add_common(sub, sub=True)
        sub.add_argument("--today", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    s = sp.add_parser("init", help="create patent/ layout, state.json, empty prior-art.json")
    _sub(s)
    s.add_argument("--title", required=True)
    s.add_argument("--mode", default="inventor", choices=ENUMS["profile.mode"])
    s.add_argument("--role", default=None, choices=ENUMS["profile.role"])
    s.add_argument("--confidentiality", default=None, choices=ENUMS["profile.confidentiality"],
                   help="abstracted (default: generic terms only in web queries) or detailed")
    s.add_argument("--force", action="store_true", help="re-create state.json if it exists")

    s = sp.add_parser("show", help="human summary: phase, verdicts, bar, open questions, next gate")
    _sub(s)

    s = sp.add_parser("set", help="set a dotted path to a JSON value (validated)")
    _sub(s)
    s.add_argument("path")
    s.add_argument("value", help="JSON value; a bare word is taken as a string")
    s.add_argument("--append", action="store_true", help="append to open_questions / depends.<file>")

    s = sp.add_parser("decide", help="record a gate decision")
    _sub(s)
    s.add_argument("--gate", required=True, help="canonical id: %s" % ", ".join(GATES))
    s.add_argument("--force-gate", action="store_true", help="allow a custom (non-canonical) gate id")
    s.add_argument("--choice", required=True)
    s.add_argument("--note", default=None)
    s.add_argument("--by", default="user")

    s = sp.add_parser("hash", help="record sha256 of artifacts (and of a downstream file's inputs)")
    _sub(s)
    s.add_argument("paths", nargs="*", help="relative paths (default: every tracked artifact)")

    s = sp.add_parser("stale", help="list downstream files whose inputs changed (exit 1 if any)")
    _sub(s)

    s = sp.add_parser("log", help="append an audit record")
    _sub(s)
    s.add_argument("--kind", required=True, choices=AUDIT_KINDS)
    s.add_argument("--json-detail", default=None, help="JSON object merged into the record")

    s = sp.add_parser("bar", help="recompute the statutory-bar status from dates")
    _sub(s)
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
