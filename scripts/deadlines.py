#!/usr/bin/env python3
"""US patent deadline math with the weekend/holiday roll (35 USC 21(b)) and a portfolio docket.

Rules come from the fenced yaml block "Machine-readable deadline rules" in
references/deadlines.md (parsed at run time by a small built-in parser; no PyYAML).
Extension fees come from references/fees.md (via fees.py). A few post-grant windows
that deadlines.md does not list (reissue broadening, PGR, IPR, 35 USC 286) are encoded
here from the statute and say so.

Examples:
    python3 scripts/deadlines.py oa --mailed 2026-02-28 --type nonfinal
    python3 scripts/deadlines.py oa --mailed 2026-02-28 --type final --entity small
    python3 scripts/deadlines.py provisional --filed 2024-02-29
    python3 scripts/deadlines.py bar --disclosed 2026-03-02
    python3 scripts/deadlines.py pct --priority 2025-06-14
    python3 scripts/deadlines.py maintenance --grant-date 2022-03-08
    python3 scripts/deadlines.py issue-fee --mailed 2026-09-10
    python3 scripts/deadlines.py reissue-broadening --grant-date 2025-05-06
    python3 scripts/deadlines.py pgr --grant-date 2026-04-07
    python3 scripts/deadlines.py ipr --grant-date 2024-04-02 --complaint-served 2026-01-15
    python3 scripts/deadlines.py damages-window --filed 2026-11-18
    python3 scripts/deadlines.py portfolio --dir patent
Every command takes --date as an alias for its base date, --today to fix "today",
and --entity to show one entity's fees (default: all three).

Conventions:
  * Months: same day-of-month N months later, else the last day of that month
    (MPEP 710.01(a); _dates.add_months). So a provisional filed 2024-02-29 has its
    12-month date on 2025-02-28 (2025 has no Feb 29), then the weekend/holiday roll.
  * Roll: Saturday, Sunday, DC federal holiday (observed), or a listed full-day USPTO
    closure -> next business day (35 USC 21(b); 37 CFR 1.7, 1.9(h)).
  * Extensions run from the UNROLLED date: the extended end date is the Office action
    date + (period + n) months, then rolled (MPEP 710.01(a): Jan 31 action, 3-month
    period due Apr 30; a 1-month extension ends May 31, whatever day Apr 30 was).

Portfolio events (portfolio.json, patentassist/portfolio@1; each {"type", "mailed"|"date"}):
  office_action (+ "action": nonfinal|final|restriction|quayle|notice_missing_parts, optional
  "ssp_months"), nonfinal_rejection, final_rejection, restriction, notice_missing_parts;
  reply_filed / response_filed / rce_filed / notice_of_appeal_filed (closes the open action);
  notice_of_allowance, issue_fee_paid; granted (or asset grant_date); maintenance_paid
  (+ "stage": 1|2|3); nonprovisional_filed / pct_filed (closes a provisional);
  national_stage_entered (closes a PCT). Assets with status abandoned/expired are skipped.

Exit codes: 0 ok; 1 portfolio has items overdue (in grace) or past every window; 2 usage error.
"""

import argparse
import datetime as _dt
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _dates import add_months, holiday_name, is_business_day, parse_date  # noqa: E402
from state import UsageError, add_common, check_schema, cli_main, finalize, finding, new_result, read_json, \
    to_namespace  # noqa: E402
import fees as _fees  # noqa: E402

SCRIPT = "deadlines.py"
DEADLINES_MD = os.path.join(os.path.dirname(HERE), "references", "deadlines.md")
SCHEMA_PORTFOLIO = "patentassist/portfolio@1"
ENTITIES = ("large", "small", "micro")


# --------------------------------------------------------------------------- mini yaml


class _Flow(object):
    """Recursive-descent parser for YAML flow collections and scalars ({a: 1, b: [x, "y"]})."""

    def __init__(self, s):
        self.s = s
        self.i = 0

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n":
            self.i += 1

    def value(self, stops):
        self.ws()
        if self.i >= len(self.s):
            return None
        c = self.s[self.i]
        if c == "{":
            return self.mapping()
        if c == "[":
            return self.seq()
        if c in "\"'":
            return self.quoted(c)
        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in stops:
            self.i += 1
        return _scalar(self.s[start:self.i].strip())

    def quoted(self, q):
        self.i += 1
        out = []
        while self.i < len(self.s):
            c = self.s[self.i]
            if q == '"' and c == "\\" and self.i + 1 < len(self.s):
                out.append(self.s[self.i + 1])
                self.i += 2
                continue
            if c == q:
                if q == "'" and self.s[self.i + 1:self.i + 2] == "'":
                    out.append("'")
                    self.i += 2
                    continue
                self.i += 1
                return "".join(out)
            out.append(c)
            self.i += 1
        raise ValueError("unterminated string")

    def mapping(self):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.i >= len(self.s):
                raise ValueError("unterminated mapping")
            if self.s[self.i] == "}":
                self.i += 1
                return out
            if self.s[self.i] in "\"'":
                key = self.quoted(self.s[self.i])
                self.ws()
            else:
                start = self.i
                while self.i < len(self.s) and self.s[self.i] != ":":
                    self.i += 1
                key = self.s[start:self.i].strip()
            if self.i >= len(self.s) or self.s[self.i] != ":":
                raise ValueError("expected ':' after key %r" % key)
            self.i += 1
            out[key] = self.value(",}")
            self.ws()
            if self.i < len(self.s) and self.s[self.i] == ",":
                self.i += 1

    def seq(self):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.i >= len(self.s):
                raise ValueError("unterminated list")
            if self.s[self.i] == "]":
                self.i += 1
                return out
            out.append(self.value(",]"))
            self.ws()
            if self.i < len(self.s) and self.s[self.i] == ",":
                self.i += 1


def _scalar(t):
    if t in ("", "~", "null", "Null", "NULL"):
        return None
    if t in ("true", "True"):
        return True
    if t in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if re.fullmatch(r"-?\d+\.\d+", t):
        return float(t)
    return t


def _strip_comment(line):
    q = None
    for i, c in enumerate(line):
        if q:
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def _balance(s):
    depth, q = 0, None
    for c in s:
        if q:
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
    return depth


def parse_mini_yaml(text):
    """Parse the simple YAML used in references/deadlines.md: block mappings and block
    sequences by indentation, whose leaves are scalars or (possibly multi-line) flow
    collections. Anchors, multi-line strings, and tags are not supported."""
    raw = [_strip_comment(l) for l in text.splitlines()]
    lines = []
    i = 0
    while i < len(raw):
        l = raw[i]
        if not l.strip():
            i += 1
            continue
        while _balance(l) > 0 and i + 1 < len(raw):
            i += 1
            l = l + " " + raw[i].strip()
        lines.append((len(l) - len(l.lstrip(" ")), l.strip()))
        i += 1

    def flow(s):
        p = _Flow(s)
        v = p.value("")
        return v

    def block(pos, indent):
        if pos >= len(lines):
            return None, pos
        if lines[pos][1].startswith("- ") or lines[pos][1] == "-":
            out = []
            while pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("-"):
                rest = lines[pos][1][1:].strip()
                pos += 1
                if rest:
                    out.append(flow(rest))
                else:
                    v, pos = block(pos, lines[pos][0]) if pos < len(lines) else (None, pos)
                    out.append(v)
            return out, pos
        out = {}
        while pos < len(lines) and lines[pos][0] == indent and not lines[pos][1].startswith("- "):
            m = re.match(r"^(\"[^\"]*\"|'[^']*'|[^:]+?)\s*:(?:\s+(.*))?$", lines[pos][1])
            if not m:
                raise ValueError("cannot parse yaml line: %r" % lines[pos][1])
            key = m.group(1).strip("\"'")
            rest = (m.group(2) or "").strip()
            pos += 1
            if rest:
                out[key] = flow(rest)
            elif pos < len(lines) and lines[pos][0] > indent:
                out[key], pos = block(pos, lines[pos][0])
            elif pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("- "):
                out[key], pos = block(pos, indent)  # "key:\n- item" at the same indent
            else:
                out[key] = None
        return out, pos

    if not lines:
        return {}
    v, _ = block(0, lines[0][0])
    return v


_RULES_CACHE = {}


def load_rules(path=None):
    """{"date_rules": {...}, "deadlines": {id: rule}, "last_verified": str} from deadlines.md."""
    path = path or DEADLINES_MD
    if path in _RULES_CACHE:
        return _RULES_CACHE[path]
    if not os.path.exists(path):
        raise UsageError("deadline rules not found: %s" % path)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    start = text.find("## Machine-readable deadline rules")
    m = re.search(r"```yaml[^\n]*\n(.*?)```", text[start if start >= 0 else 0:], re.S)
    if not m:
        raise UsageError("no ```yaml deadline block in %s" % path)
    data = parse_mini_yaml(m.group(1))
    rules = {}
    for r in data.get("deadlines") or []:
        if isinstance(r, dict) and r.get("id"):
            rules[r["id"]] = r
    fm = re.search(r"^last_verified:\s*(\S+)", text, re.M)
    out = {"date_rules": data.get("date_rules") or {}, "deadlines": rules,
           "last_verified": fm.group(1) if fm else "unknown", "source_path": path}
    _RULES_CACHE[path] = out
    return out


def rule(rid, path=None):
    r = load_rules(path)["deadlines"].get(rid)
    if r is None:
        raise UsageError("rule %r not found in references/deadlines.md" % rid)
    return r


# --------------------------------------------------------------------------- date helpers


def closures(path=None):
    out = set()
    for d in load_rules(path)["date_rules"].get("ad_hoc_closures") or []:
        try:
            out.add(parse_date(str(d)))
        except ValueError:
            pass
    return out


def closed_reason(d, extra=()):
    if d.weekday() == 5:
        return "Saturday"
    if d.weekday() == 6:
        return "Sunday"
    h = holiday_name(d)
    if h:
        return h
    if d in extra:
        return "USPTO closed (ad hoc closure)"
    return None


def roll(d, extra=None):
    """(rolled_date, [reasons]) under 35 USC 21(b): skip weekends, DC federal holidays, closures."""
    extra = closures() if extra is None else extra
    reasons = []
    while not is_business_day(d) or d in extra:
        reasons.append("%s %s" % (d.isoformat(), closed_reason(d, extra)))
        d = d + _dt.timedelta(days=1)
    return d, reasons


def offset_date(base, off):
    """Apply {years, months, days} to a date (months per add_months)."""
    off = off or {}
    months = int(off.get("years", 0) or 0) * 12 + int(off.get("months", 0) or 0)
    d = add_months(base, months) if months else base
    if off.get("days"):
        d = d + _dt.timedelta(days=int(off["days"]))
    return d


def _fmt(d):
    return "%s (%s)" % (d.isoformat(), d.strftime("%a"))


def dated(label, unrolled, do_roll=True, today=None, note=None):
    """A single computed date with its roll and days-left."""
    if do_roll:
        rolled, why = roll(unrolled)
    else:
        rolled, why = unrolled, []
    out = {"label": label, "unrolled": unrolled.isoformat(), "date": rolled.isoformat(),
           "weekday": rolled.strftime("%a"), "rolled": rolled != unrolled, "roll_reason": why,
           "roll_applies": bool(do_roll)}
    if today:
        out["days_left"] = (rolled - today).days
    if note:
        out["note"] = note
    return out


def _fee_amounts(key, entity=None):
    table = _fees.load_fee_table()
    row = _fees.amounts(table, key)
    cfr = _fees.fee_row(table, key).get("cfr")
    return {"key": key, "cfr": cfr, "amounts": ({entity: row[entity]} if entity else row)}


def _fee_text(f):
    return "%s %s" % (" / ".join("%s %s" % (e, _fees.money(v)) for e, v in f["amounts"].items()),
                      "[%s]" % f["cfr"])


def _today(a):
    return parse_date(a.today) if a.today else _dt.date.today()


def _base(a, *names):
    for n in names + ("date",):
        v = getattr(a, n, None)
        if v:
            try:
                return parse_date(v)
            except ValueError:
                raise UsageError("bad date for --%s: %r (use YYYY-MM-DD)" % (n.replace("_", "-"), v))
    raise UsageError("give --%s YYYY-MM-DD" % names[0].replace("_", "-"))


# --------------------------------------------------------------------------- calculators


OA_TYPES = {
    "nonfinal": ("nonfinal_oa_reply", "Non-final Office action reply"),
    "final": ("final_rejection_reply", "Final rejection reply"),
    "restriction": ("restriction_reply", "Restriction/election reply"),
    "quayle": ("quayle_reply", "Ex parte Quayle action reply"),
    "notice_missing_parts": ("missing_parts_notice", "Notice to File Missing Parts reply"),
    "notice_of_allowance": ("issue_fee", "Issue fee (Notice of Allowance)"),
}


def reply_deadline(mailed, oa_type, ssp_months=None, today=None, entity=None, provisional=False):
    """Reply period with each extension month and the statutory cap, all rolled."""
    if oa_type not in OA_TYPES:
        raise UsageError("--type must be one of %s" % ", ".join(OA_TYPES))
    rid, label = OA_TYPES[oa_type]
    r = rule(rid)
    ssp = int(ssp_months) if ssp_months else int((r.get("offset") or {}).get("months", 3))
    if not 1 <= ssp <= 6:
        raise UsageError("--ssp-months must be 1-6")
    item = {"id": rid, "kind": oa_type, "label": label, "base_label": "mailed", "base_date": mailed.isoformat(),
            "basis": r.get("basis"), "period_months": ssp, "ext": r.get("ext"), "notes": []}
    if ssp_months and int(ssp_months) != int((r.get("offset") or {}).get("months", ssp)):
        item["notes"].append("Period set by --ssp-months (%d) instead of the rule default (%s months)."
                             % (ssp, (r.get("offset") or {}).get("months")))
    unrolled = add_months(mailed, ssp)
    item["due"] = dated("Period ends (no extension fee)", unrolled, r.get("roll", True) is True, today)
    item["extensions"] = []
    ext = r.get("ext")
    cap_m = r.get("max_from_trigger_months")
    if ext == "1.136(a)":
        max_ext = 5
        if cap_m:
            max_ext = min(5, int(cap_m) - ssp)
        for n in range(1, max_ext + 1):
            e = dated("+%d month%s" % (n, "" if n == 1 else "s"), add_months(mailed, ssp + n), True, today)
            e["months"] = n
            e["fee"] = _fee_amounts(_fees.extension_key(n, provisional=provisional), entity)
            item["extensions"].append(e)
        if cap_m:
            item["cap"] = dated("Absolute limit, %d months from mailing (35 USC 133; 37 CFR 1.136(a))" % int(cap_m),
                                add_months(mailed, int(cap_m)), True, today)
        else:
            item["notes"].append("No 6-month statutory cap is listed for this rule; 1.136(a) allows up to 5 months "
                                 "of extension unless the notice says otherwise.")
        item["notes"].append("Extension end dates run from the unrolled period end (mailing date + period + n months), "
                             "then roll (MPEP 710.01(a)). The fee is set by the month in which the reply is filed.")
    elif ext in ("none", None):
        item["notes"].append("Not extendable (%s)." % (r.get("basis") or "rule"))
    else:
        item["notes"].append("Extension only under %s." % ext)
    if oa_type == "final":
        two = dated("First reply within 2 months (advisory-action date)", add_months(mailed, 2), True, today)
        item["advisory_date"] = two
        item["notes"].append("Final: if the first reply is filed by %s, the period ends at the later of the 3-month "
                             "date or the advisory action's mailing date, and extension fees run from that date "
                             "(MPEP 706.07(f)). A notice of appeal is due within the same reply period (41.31(a)(1)). "
                             "AFCP 2.0 has ended (no requests after Dec 14, 2024)." % two["date"])
    if oa_type == "restriction":
        item["notes"].append("Reply with an election (and any traverse); you can file a divisional later.")
    if oa_type == "notice_of_allowance":
        item["notes"].append("A postponed inventor declaration is due no later than issue fee payment "
                             "(1.53(f)(3)(ii)). An IDS after allowance needs the 1.97(d) statement and fee.")
        item["fee"] = _fee_amounts("utility_issue", entity)
    if oa_type == "notice_missing_parts":
        item["notes"].append("The period is the one set in the notice (usually 2 months); pass --ssp-months if "
                             "different. The 1.16(f) surcharge is due within this period if the declaration or "
                             "fees were late.")
    return item


def provisional_deadlines(filed, today=None, entity=None):
    r = rule("provisional_to_nonprovisional")
    unrolled = offset_date(filed, r.get("offset"))
    item = {"id": r["id"], "kind": "provisional", "label": "Nonprovisional and/or PCT claiming the provisional",
            "base_label": "provisional filed", "base_date": filed.isoformat(), "basis": r.get("basis"),
            "ext": r.get("ext"), "notes": []}
    item["due"] = dated("12-month date (nonprovisional under 119(e) / PCT priority)", unrolled, True, today)
    item["reminders"] = [dated("9-month reminder: decide on nonprovisional / PCT / foreign", add_months(filed, 9),
                               False, today),
                         dated("11-month reminder: filing package final", add_months(filed, 11), False, today)]
    rest = r.get("restore") or {}
    wm = int(rest.get("window_months", 2))
    rd = dated("Restoration window ends (petition, unintentional delay)", add_months(unrolled, wm), False, today,
               note="computed from the UNROLLED 12-month date (whether the base is rolled is unconfirmed; "
                    "this is the safe date)")
    rd["fee"] = _fee_amounts(rest.get("fee", "petition_restore_priority"), entity)
    rd["petition"] = rest.get("petition")
    item["restore"] = rd
    b = rule("benefit_claim_in_ads")
    offs = b.get("offset") or [{}, {}]
    item["benefit_claim"] = dated("Benefit claim in the ADS: later of 4 months from the nonprovisional filing or "
                                  "this 16-month date", offset_date(filed, offs[1] if len(offs) > 1 else {"months": 16}),
                                  True, today, note=b.get("basis"))
    if filed.month == 2 and filed.day == 29:
        item["notes"].append("Filed on Feb 29: the 12-month date is Feb 28 of the next year (same day-of-month, or "
                             "the last day of the month when it does not exist; MPEP 710.01(a); _dates.add_months), "
                             "then rolled if Feb 28 is a weekend or holiday.")
    item["notes"].append("The 12-month date cannot be extended (%s). It rolls under 35 USC 119(e)(3) / 37 CFR 1.7(b). "
                         "A PCT application claiming the provisional has the same 12-month limit; its weekend roll "
                         "follows the receiving office (PCT Rule 80.5)." % (r.get("basis")))
    item["notes"].append("Filing the nonprovisional does not need the provisional's claims; everything claimed must be "
                         "supported in the provisional to get its date.")
    return item


def bar_deadline(disclosed, today=None):
    unrolled = add_months(disclosed, 12)
    item = {"id": "grace_period_102b1", "kind": "bar", "label": "US filing deadline after the inventor's own disclosure",
            "base_label": "first public disclosure / sale / offer / public use", "base_date": disclosed.isoformat(),
            "basis": "35 USC 102(b)(1)(A); 35 USC 21(b)", "ext": "none", "notes": []}
    item["due"] = dated("Last day to file in the US (1-year grace period)", unrolled, True, today)
    item["safe_date"] = unrolled.isoformat()
    item["notes"].append("Safe course: file by the unrolled date %s. The roll under 35 USC 21(b) follows state.py's "
                         "bar clock; it is not in references/deadlines.md's table." % unrolled.isoformat())
    item["notes"].append("The exception covers only the inventor's own disclosure (or one derived from the inventor), "
                         "not an independent third party's.")
    item["notes"].append("Most foreign offices require absolute novelty: a public disclosure before filing likely ends "
                         "foreign rights now, whatever the US grace period says.")
    return item


def pct_deadlines(priority, today=None):
    r30 = rule("pct_national_stage_us")
    r31 = rule("pct_regional_phase_epo")
    item = {"id": "pct", "kind": "pct", "label": "PCT national / regional phase", "base_label": "priority date",
            "base_date": priority.isoformat(), "basis": "%s; %s" % (r30.get("basis"), r31.get("basis")),
            "ext": "none", "notes": []}
    item["due"] = dated("US national stage, 30 months (%s)" % r30.get("basis"), offset_date(priority, r30["offset"]),
                        True, today)
    item["others"] = [dated("EPO regional phase, 31 months (%s)" % r31.get("basis"), offset_date(priority, r31["offset"]),
                            False, today, note="EPO's own extension to the next EPO working day is not modeled; "
                                               "unrolled date shown")]
    item["notes"].append("The US 30-month date may not be extended (1.495). Late entry needs a petition to revive "
                         "(1.137, 1.17(m)). Other offices: usually 30 or 31 months (check each).")
    return item


def maintenance_window(grant, rid, today=None):
    """One maintenance stage from deadlines.md: open, last day without surcharge, end of grace."""
    grant = parse_date(grant)
    today = parse_date(today) if today else None
    r = rule(rid)
    opened = offset_date(grant, r.get("window_open"))
    due_u = offset_date(grant, r.get("due"))
    grace_u = offset_date(grant, r.get("grace_end"))
    do_roll = r.get("roll", True) is True
    due_r, due_why = roll(due_u) if do_roll else (due_u, [])
    grace_r, grace_why = roll(grace_u) if do_roll else (grace_u, [])
    years = (r.get("due") or {}).get("years", 0)
    label = "%s.5-year fee" % years
    out = {"id": rid, "label": label, "basis": r.get("basis"), "window_open": opened.isoformat(),
           "due_unrolled": due_u.isoformat(), "due": due_r.isoformat(), "due_rolled": due_r != due_u,
           "due_roll_reason": due_why, "grace_end_unrolled": grace_u.isoformat(), "grace_end": grace_r.isoformat(),
           "grace_rolled": grace_r != grace_u, "grace_roll_reason": grace_why,
           "surcharge_from": (due_r + _dt.timedelta(days=1)).isoformat(),
           "expires_if_unpaid": "end of %s (anniversary date; 1.362(g))" % grace_u.isoformat(),
           "surcharge_key": r.get("surcharge_in_grace")}
    if today:
        if today < opened:
            st = "not open yet"
        elif today <= due_r:
            st = "open: pay without surcharge"
        elif today <= grace_r:
            st = "IN GRACE: surcharge due"
        else:
            st = "PAST GRACE: expired unless paid (petition 1.378)"
        out["status"] = st
        out["days_to_due"] = (due_r - today).days
        out["days_to_grace_end"] = (grace_r - today).days
    else:
        out["status"] = "n/a"
    return out


def maintenance_deadlines(grant, today=None, entity=None):
    item = {"id": "maintenance", "kind": "maintenance", "label": "Maintenance fees (utility patents)",
            "base_label": "grant date", "base_date": grant.isoformat(), "basis": "37 CFR 1.362; 1.20(e)-(h)",
            "ext": "grace only", "stages": [], "notes": []}
    for rid, fkey in (("maintenance_1", "maintenance_3_5y"), ("maintenance_2", "maintenance_7_5y"),
                      ("maintenance_3", "maintenance_11_5y")):
        w = maintenance_window(grant, rid, today)
        w["fee"] = _fee_amounts(fkey, entity)
        w["surcharge"] = _fee_amounts(w.get("surcharge_key") or "maintenance_grace_surcharge", entity)
        item["stages"].append(w)
    item["notes"].append("Window and grace end dates roll under 1.362(f). Payment before the window opens is not "
                         "accepted. For a reissue, count from the original patent's grant (1.362(h)).")
    item["notes"].append("Small/micro status must be re-checked before each payment (1.27(g), 1.29).")
    return item


EXTRA_RULES = {
    "reissue_broadening": {"offset": {"years": 2}, "roll": True,
                           "basis": "35 USC 251(d); 35 USC 21(b) (not in references/deadlines.md)"},
    "pgr_petition": {"offset": {"months": 9}, "roll": True,
                     "basis": "35 USC 321(c); 37 CFR 42.202(a) (not in references/deadlines.md)"},
    "ipr_earliest": {"offset": {"months": 9}, "roll": False,
                     "basis": "35 USC 311(c); 37 CFR 42.102(a) (not in references/deadlines.md)"},
    "ipr_315b_bar": {"offset": {"years": 1}, "roll": True,
                     "basis": "35 USC 315(b) (not in references/deadlines.md)"},
    "damages_286": {"offset": {"years": -6}, "roll": False, "basis": "35 USC 286 (not in references/deadlines.md)"},
}


def reissue_deadline(grant, today=None):
    r = EXTRA_RULES["reissue_broadening"]
    item = {"id": "reissue_broadening", "kind": "reissue-broadening", "label": "Broadening reissue application",
            "base_label": "grant date", "base_date": grant.isoformat(), "basis": r["basis"], "ext": "none", "notes": []}
    item["due"] = dated("Last day to file a broadening reissue (2 years from grant)", offset_date(grant, r["offset"]),
                        True, today)
    item["notes"].append("The application must show the intent to broaden within the 2 years; narrowing reissues "
                         "have no such limit. Safe date: the unrolled %s." % item["due"]["unrolled"])
    return item


def pgr_deadline(grant, today=None):
    r = EXTRA_RULES["pgr_petition"]
    item = {"id": "pgr", "kind": "pgr", "label": "Post-grant review petition window", "base_label": "grant/reissue date",
            "base_date": grant.isoformat(), "basis": r["basis"], "ext": "none", "notes": []}
    item["due"] = dated("Last day to petition for PGR (9 months from grant)", offset_date(grant, r["offset"]), True, today)
    item["notes"].append("PGR is open only for patents under the AIA first-inventor-to-file rules (effective filing "
                         "date on or after Mar 16, 2013). Applying the 21(b) roll to the PGR window is an assumption; "
                         "file by the unrolled date %s to be safe." % item["due"]["unrolled"])
    return item


def ipr_deadlines(grant, served=None, today=None):
    r = EXTRA_RULES["ipr_earliest"]
    item = {"id": "ipr", "kind": "ipr", "label": "Inter partes review timing", "base_label": "grant date",
            "base_date": grant.isoformat(), "basis": r["basis"], "ext": "none", "notes": []}
    nine = offset_date(grant, r["offset"])
    first = nine + _dt.timedelta(days=1)
    item["earliest"] = dated("Earliest IPR filing (AIA patent): after the 9-month date %s, or after any instituted PGR "
                             "ends, whichever is later" % nine.isoformat(), first, False, today)
    item["notes"].append("35 USC 311(c) says 'after' the 9-month date; the day after is shown to be safe. Patents "
                         "outside the AIA first-inventor-to-file rules have no 9-month wait (42.102(a)).")
    if served:
        b = EXTRA_RULES["ipr_315b_bar"]
        item["due"] = dated("Last day before the 315(b) time bar (1 year from service of the complaint)",
                            offset_date(served, b["offset"]), True, today)
        item["served"] = served.isoformat()
        item["basis"] += "; " + b["basis"]
        item["notes"].append("A petition filed more than 1 year after the petitioner, real party in interest, or privy "
                             "was served with an infringement complaint is barred. The PTAB has applied the 21(b) "
                             "roll to this bar; the unrolled date %s is the safe date." % item["due"]["unrolled"])
    else:
        item["notes"].append("Pass --complaint-served D for the 1-year 315(b) bar.")
    return item


def damages_window(filed, today=None):
    r = EXTRA_RULES["damages_286"]
    start = offset_date(filed, r["offset"])
    item = {"id": "damages_286", "kind": "damages-window", "label": "Past-damages window (35 USC 286)",
            "base_label": "complaint or counterclaim filed", "base_date": filed.isoformat(), "basis": r["basis"],
            "ext": "none", "notes": []}
    item["due"] = dated("Earliest infringement date still recoverable (six years before filing)", start, False, today)
    item["notes"].append("No recovery for infringement committed more than six years before the complaint or "
                         "counterclaim. This is a court limit: no USPTO weekend/holiday roll. The exact boundary day "
                         "(and a Feb 29 base, clamped to Feb 28) is unconfirmed; treat it as approximate by a day.")
    item["notes"].append("Marking or actual notice (35 USC 287(a)) and the patent's grant date can cut the window "
                         "further.")
    return item


# --------------------------------------------------------------------------- portfolio


OA_EVENT_TYPES = {
    "office_action": None, "oa": None, "nonfinal": "nonfinal", "nonfinal_rejection": "nonfinal",
    "non_final_rejection": "nonfinal", "final": "final", "final_rejection": "final", "restriction": "restriction",
    "restriction_requirement": "restriction", "election": "restriction", "quayle": "quayle",
    "notice_missing_parts": "notice_missing_parts", "missing_parts": "notice_missing_parts",
}
REPLY_EVENTS = {"reply_filed", "response_filed", "reply", "response", "rce_filed", "rce", "amendment_filed",
                "notice_of_appeal_filed", "appeal_filed", "missing_parts_filed"}
ALLOW_EVENTS = {"notice_of_allowance", "allowance", "noa"}
ISSUE_FEE_EVENTS = {"issue_fee_paid", "issue_fee"}
GRANT_EVENTS = {"granted", "grant", "issued", "issue"}
MAINT_EVENTS = {"maintenance_paid", "maintenance_fee_paid", "maintenance"}
CONVERT_EVENTS = {"nonprovisional_filed", "converted", "pct_filed", "conversion_filed"}
NATIONAL_EVENTS = {"national_stage_entered", "national_stage_filed", "371_filed"}
END_STATUSES = {"abandoned", "expired", "lapsed", "withdrawn"}


def _ev_date(e):
    for k in ("mailed", "date", "filed", "paid"):
        v = e.get(k)
        if v:
            try:
                return parse_date(v)
            except ValueError:
                return None
    return None


def _group_for(date_s, today, in_grace=False, lapsed=False):
    if lapsed:
        return "past_all_windows"
    if in_grace:
        return "overdue_in_grace"
    d = parse_date(date_s)
    left = (d - today).days
    if left <= 30:
        return "due_30"
    if left <= 90:
        return "due_90"
    return "later"


def _asset_deadlines(asset, today, missing):
    """Recompute next deadlines for one asset from its events. Returns a list of entries."""
    aid = asset.get("id") or asset.get("app_no") or asset.get("patent_no") or "?"
    title = asset.get("title") or ""
    entity = asset.get("entity") if asset.get("entity") in ENTITIES else None
    status = (asset.get("status") or "").lower()
    atype = (asset.get("type") or "").lower()
    out = []

    def add(kind, date_s, label, basis, group, extra=None):
        e = {"asset": aid, "title": title, "kind": kind, "date": date_s, "label": label, "basis": basis,
             "group": group, "days_left": (parse_date(date_s) - today).days if date_s else None}
        if extra:
            e.update(extra)
        out.append(e)

    if status in END_STATUSES:
        return out
    events = []
    for e in asset.get("events") or []:
        if not isinstance(e, dict):
            continue
        d = _ev_date(e)
        t = (e.get("type") or "").lower()
        if d is None:
            missing.append({"asset": aid, "title": title, "reason": "event %r has no readable date" % (t or "?")})
            continue
        events.append((d, t, e))
    events.sort(key=lambda x: x[0])
    types = set(t for _, t, _ in events)

    # Provisional -> conversion
    if atype == "provisional" or status == "provisional":
        if types & CONVERT_EVENTS:
            return out
        fd = asset.get("filing_date")
        if not fd:
            missing.append({"asset": aid, "title": title, "reason": "provisional with no filing_date"})
            return out
        p = provisional_deadlines(parse_date(fd), today, entity)
        due, rest = parse_date(p["due"]["date"]), parse_date(p["restore"]["date"])
        if today <= due:
            add("provisional_12_month", p["due"]["date"], p["label"], p["basis"], _group_for(p["due"]["date"], today),
                {"rolled": p["due"]["rolled"]})
        elif today <= rest:
            add("provisional_restoration", p["restore"]["date"], "12-month date %s passed; restoration petition "
                "window (1.78(b))" % p["due"]["date"], p["basis"], "overdue_in_grace", {"fee": p["restore"]["fee"]})
        else:
            add("provisional_lapsed", p["restore"]["date"], "Provisional benefit lost (12 months + 2-month restoration "
                "passed)", p["basis"], "past_all_windows")
        return out

    # PCT -> national stage
    if atype == "pct":
        if types & NATIONAL_EVENTS:
            return out
        pd = asset.get("priority_date") or asset.get("filing_date")
        if not pd:
            missing.append({"asset": aid, "title": title, "reason": "PCT with no priority_date"})
            return out
        p = pct_deadlines(parse_date(pd), today)
        lapsed = today > parse_date(p["due"]["date"])
        add("pct_30_month", p["due"]["date"], "US national stage (30 months)", "37 CFR 1.495",
            _group_for(p["due"]["date"], today, lapsed=lapsed))
        return out

    grant = asset.get("grant_date")
    for d, t, e in events:
        if t in GRANT_EVENTS and not grant:
            grant = d.isoformat()
    if grant or status in ("granted", "issued", "patented"):
        if not grant:
            missing.append({"asset": aid, "title": title, "reason": "granted but no grant_date"})
            return out
        paid = set()
        for d, t, e in events:
            if t in MAINT_EVENTS:
                st = e.get("stage")
                if st in (1, 2, 3, "1", "2", "3"):
                    paid.add(int(st))
                else:
                    missing.append({"asset": aid, "title": title,
                                    "reason": "maintenance payment on %s has no stage (1, 2 or 3)" % d.isoformat()})
        for stage, rid, fkey in ((1, "maintenance_1", "maintenance_3_5y"), (2, "maintenance_2", "maintenance_7_5y"),
                                 (3, "maintenance_3", "maintenance_11_5y")):
            if stage in paid:
                continue
            w = maintenance_window(grant, rid, today)
            fee = _fee_amounts(fkey, entity)
            if today <= parse_date(w["due"]):
                add("maintenance_%d" % stage, w["due"], "%s (window opens %s)" % (w["label"], w["window_open"]),
                    w["basis"], _group_for(w["due"], today), {"fee": fee, "window_open": w["window_open"]})
            elif today <= parse_date(w["grace_end"]):
                add("maintenance_%d" % stage, w["grace_end"], "%s IN GRACE: surcharge due; patent expires if unpaid by "
                    "%s" % (w["label"], w["grace_end"]), w["basis"], "overdue_in_grace",
                    {"fee": fee, "surcharge": _fee_amounts("maintenance_grace_surcharge", entity)})
            else:
                add("maintenance_%d" % stage, w["grace_end"], "%s unpaid after grace: patent expired unless paid "
                    "(check Patent Center; petition 1.378)" % w["label"], w["basis"], "past_all_windows")
            break  # only the next unpaid stage matters
        return out

    # Pending application: allowance, then office actions
    last_allow = max([d for d, t, _ in events if t in ALLOW_EVENTS] or [None], key=lambda x: x or _dt.date.min)
    if last_allow:
        if not any(t in ISSUE_FEE_EVENTS and d >= last_allow for d, t, _ in events):
            it = reply_deadline(last_allow, "notice_of_allowance", today=today, entity=entity)
            due = it["due"]["date"]
            add("issue_fee", due, "Issue fee (Notice of Allowance mailed %s; not extendable)" % last_allow.isoformat(),
                it["basis"], _group_for(due, today, lapsed=today > parse_date(due)), {"fee": it.get("fee")})
        return out
    oas = [(d, t, e) for d, t, e in events if t in OA_EVENT_TYPES]
    if oas:
        d, t, e = oas[-1]
        replied = any(tt in REPLY_EVENTS and dd >= d for dd, tt, _ in events)
        if not replied:
            kind = OA_EVENT_TYPES[t] or (e.get("action") or e.get("subtype") or e.get("kind") or "").lower() or None
            kind = {"non-final": "nonfinal", "non_final": "nonfinal"}.get(kind, kind)
            if kind not in OA_TYPES:
                missing.append({"asset": aid, "title": title,
                                "reason": "office action on %s: type unknown (set action: nonfinal|final|restriction)"
                                          % d.isoformat()})
                return out
            it = reply_deadline(d, kind, e.get("ssp_months"), today, entity)
            due = parse_date(it["due"]["date"])
            cap = parse_date(it["cap"]["date"]) if it.get("cap") else (
                parse_date(it["extensions"][-1]["date"]) if it["extensions"] else due)
            if today <= due:
                add("oa_reply", it["due"]["date"], "%s (mailed %s)" % (it["label"], d.isoformat()), it["basis"],
                    _group_for(it["due"]["date"], today), {"extendable_to": cap.isoformat()})
            elif today <= cap:
                nxt = next((x for x in it["extensions"] if today <= parse_date(x["date"])), None)
                add("oa_reply", nxt["date"] if nxt else cap.isoformat(),
                    "%s (mailed %s) past %s: reply with a %d-month extension by %s" % (
                        it["label"], d.isoformat(), it["due"]["date"], nxt["months"] if nxt else 0,
                        nxt["date"] if nxt else cap.isoformat()), it["basis"], "overdue_in_grace",
                    {"fee": nxt["fee"] if nxt else None, "absolute_limit": cap.isoformat()})
            else:
                add("oa_reply", cap.isoformat(), "%s (mailed %s): every reply window passed; abandoned unless a reply "
                    "was filed (check Patent Center; revival 1.137)" % (it["label"], d.isoformat()), it["basis"],
                    "past_all_windows")
        return out
    if not asset.get("filing_date"):
        missing.append({"asset": aid, "title": title, "reason": "no filing_date and no events"})
    else:
        missing.append({"asset": aid, "title": title, "reason": "pending with no office action, allowance, or grant "
                                                                 "recorded: nothing to compute"})
    return out


GROUP_ORDER = [("past_all_windows", "PAST EVERY WINDOW (verify, likely lapsed)"),
               ("overdue_in_grace", "OVERDUE BUT IN GRACE / EXTENSION"),
               ("due_30", "DUE WITHIN 30 DAYS"), ("due_90", "DUE WITHIN 90 DAYS"), ("later", "LATER")]


def portfolio(dirpath, today, path=None):
    p = path or os.path.join(dirpath, "portfolio.json")
    if not os.path.exists(p):
        raise UsageError("portfolio file not found: %s" % p)
    try:
        data = read_json(p)
    except ValueError as e:
        raise UsageError("portfolio.json is not valid JSON: %s" % e)
    check_schema(data, SCHEMA_PORTFOLIO, p)
    entries, missing = [], []
    for asset in data.get("assets") or []:
        if isinstance(asset, dict):
            entries.extend(_asset_deadlines(asset, today, missing))
    groups = {g: [] for g, _ in GROUP_ORDER}
    for e in sorted(entries, key=lambda x: (x["date"] or "9999")):
        groups[e["group"]].append(e)
    groups["missing_data"] = missing
    return groups


# --------------------------------------------------------------------------- output


def _date_line(d, indent="  "):
    s = "%s%s: %s" % (indent, d["label"], _fmt(parse_date(d["date"])))
    if d.get("rolled"):
        s += "  ROLLED from %s (%s; 35 USC 21(b))" % (d["unrolled"], "; ".join(d["roll_reason"]))
    elif d.get("roll_applies") is False:
        s += "  (no roll applied)"
    else:
        s += "  (no roll needed)"
    if d.get("days_left") is not None:
        s += "  [%s]" % ("%d days left" % d["days_left"] if d["days_left"] >= 0 else "%d days ago" % -d["days_left"])
    return s


def render(item, lines):
    lines.append("%s  [%s]" % (item["label"], item.get("basis") or ""))
    lines.append("  Base date (%s): %s" % (item["base_label"], _fmt(parse_date(item["base_date"]))))
    if item.get("period_months"):
        lines.append("  Period: %d month(s); extension: %s" % (item["period_months"], item.get("ext")))
    if item.get("due"):
        lines.append(_date_line(item["due"]))
    if item.get("fee"):
        lines.append("    fee: " + _fee_text(item["fee"]))
    if item.get("advisory_date"):
        lines.append(_date_line(item["advisory_date"]))
    for e in item.get("extensions") or []:
        lines.append(_date_line(e, "    ") + "  fee " + _fee_text(e["fee"]))
    if item.get("cap"):
        lines.append(_date_line(item["cap"]))
    for key in ("earliest", "benefit_claim", "restore"):
        if item.get(key):
            lines.append(_date_line(item[key]))
            if item[key].get("fee"):
                lines.append("    fee: " + _fee_text(item[key]["fee"]))
            if item[key].get("note"):
                lines.append("    note: " + item[key]["note"])
    for r in item.get("reminders") or []:
        lines.append(_date_line(r))
    for o in item.get("others") or []:
        lines.append(_date_line(o))
        if o.get("note"):
            lines.append("    note: " + o["note"])
    for s in item.get("stages") or []:
        lines.append("  %s [%s]: window opens %s; last day without surcharge %s%s; grace through %s%s; %s" % (
            s["label"], s["fee"]["cfr"], s["window_open"], _fmt(parse_date(s["due"])),
            (" ROLLED from %s (%s)" % (s["due_unrolled"], "; ".join(s["due_roll_reason"]))) if s["due_rolled"] else "",
            _fmt(parse_date(s["grace_end"])),
            (" ROLLED from %s (%s)" % (s["grace_end_unrolled"], "; ".join(s["grace_roll_reason"])))
            if s["grace_rolled"] else "", s["status"]))
        lines.append("    fee %s; grace surcharge %s" % (_fee_text(s["fee"]), _fee_text(s["surcharge"])))
    if item.get("safe_date"):
        lines.append("  Safe date (unrolled): %s" % item["safe_date"])
    for n in item.get("notes") or []:
        lines.append("  - " + n)


# --------------------------------------------------------------------------- commands


def _single(a, res, item):
    res["deadline"] = item
    render(item, res["text"])


def cmd_oa(a, res):
    if not a.type:
        raise UsageError("give --type nonfinal|final|restriction|notice_missing_parts|notice_of_allowance")
    _single(a, res, reply_deadline(_base(a, "mailed"), a.type, a.ssp_months, _today(a), a.entity, a.provisional))


def cmd_provisional(a, res):
    _single(a, res, provisional_deadlines(_base(a, "filed"), _today(a), a.entity))


def cmd_bar(a, res):
    _single(a, res, bar_deadline(_base(a, "disclosed"), _today(a)))


def cmd_pct(a, res):
    _single(a, res, pct_deadlines(_base(a, "priority"), _today(a)))


def cmd_maintenance(a, res):
    _single(a, res, maintenance_deadlines(_base(a, "grant_date"), _today(a), a.entity))


def cmd_issue_fee(a, res):
    _single(a, res, reply_deadline(_base(a, "mailed"), "notice_of_allowance", None, _today(a), a.entity))


def cmd_reissue(a, res):
    _single(a, res, reissue_deadline(_base(a, "grant_date"), _today(a)))


def cmd_pgr(a, res):
    _single(a, res, pgr_deadline(_base(a, "grant_date"), _today(a)))


def cmd_ipr(a, res):
    served = parse_date(a.complaint_served) if a.complaint_served else None
    _single(a, res, ipr_deadlines(_base(a, "grant_date"), served, _today(a)))


def cmd_damages(a, res):
    _single(a, res, damages_window(_base(a, "filed"), _today(a)))


def cmd_portfolio(a, res):
    today = _today(a)
    groups = portfolio(a.dir, today, a.file)
    res["groups"] = groups
    res["today"] = today.isoformat()
    res["text"].append("Docket as of %s (computed from events in %s; verify against Patent Center before acting)"
                       % (today.isoformat(), a.file or os.path.join(a.dir, "portfolio.json")))
    for g, title in GROUP_ORDER:
        res["text"].append("%s (%d)" % (title, len(groups[g])))
        for e in groups[g]:
            line = "  %s  %-10s %s  %s [%s]" % (e["date"], e["asset"], e["title"][:40], e["label"], e["basis"])
            if e.get("fee"):
                line += "  fee " + _fee_text(e["fee"])
            res["text"].append(line)
            if g in ("past_all_windows", "overdue_in_grace"):
                res["findings"].append(finding("BLOCK" if g == "past_all_windows" else "WARN",
                                               g.upper(), e["asset"], "%s: %s" % (e["date"], e["label"])))
    res["text"].append("MISSING DATA (%d)" % len(groups["missing_data"]))
    for m in groups["missing_data"]:
        res["text"].append("  %-10s %s  %s" % (m["asset"], m["title"][:40], m["reason"]))
        res["findings"].append(finding("WARN", "MISSING_DATA", m["asset"], m["reason"]))
    res["summary"] = {g: len(v) for g, v in groups.items()}
    if groups["overdue_in_grace"] and res.get("exit_code", 0) == 0:
        res["exit_code"] = 1
    res["checks_run"].append("portfolio")


COMMANDS = {"oa": cmd_oa, "provisional": cmd_provisional, "bar": cmd_bar, "pct": cmd_pct,
            "maintenance": cmd_maintenance, "issue-fee": cmd_issue_fee, "reissue-broadening": cmd_reissue,
            "pgr": cmd_pgr, "ipr": cmd_ipr, "damages-window": cmd_damages, "portfolio": cmd_portfolio}

DEFAULTS = {"command": None, "dir": "patent", "json": False, "no_audit": True, "today": None, "entity": None,
            "date": None, "mailed": None, "type": None, "ssp_months": None, "provisional": False, "filed": None,
            "disclosed": None, "priority": None, "grant_date": None, "complaint_served": None, "file": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.command not in COMMANDS:
        raise UsageError("command must be one of %s" % ", ".join(COMMANDS))
    if a.entity is not None and a.entity not in ENTITIES:
        raise UsageError("--entity must be large, small, or micro")
    res = new_result()
    res["command"] = a.command
    COMMANDS[a.command](a, res)
    rules = load_rules()
    table = _fees.load_fee_table()
    res["rules_last_verified"] = rules["last_verified"]
    res["fees_last_verified"] = table["last_verified"]
    res["text"].append("Rules: references/deadlines.md (last verified %s). Fees: references/fees.md. %s"
                       % (rules["last_verified"], _fees.verify_line(table)))
    res["text"].append("The USPTO record (Patent Center) is the truth; full-day USPTO closures not listed in "
                       "deadlines.md are not applied.")
    if a.command != "portfolio":
        res["checks_run"].append(a.command)
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="deadlines.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    add_common(p)
    p.add_argument("--today", default=None, help="override today's date (YYYY-MM-DD) for testing")
    sp = p.add_subparsers(dest="command")

    def sub(name, help_, base=None):
        s = sp.add_parser(name, help=help_)
        add_common(s, sub=True)
        s.add_argument("--today", default=argparse.SUPPRESS, help="override today's date")
        s.add_argument("--entity", choices=ENTITIES, default=None, help="show one entity's fees")
        s.add_argument("--date", default=None, help="alias for the base date")
        if base:
            s.add_argument("--" + base, dest=base.replace("-", "_"), default=None)
        return s

    s = sub("oa", "Office action reply deadline with extensions", "mailed")
    s.add_argument("--type", choices=sorted(OA_TYPES), default=None)
    s.add_argument("--ssp-months", type=int, choices=(1, 2, 3, 4, 5, 6), default=None,
                   help="shortened statutory period set in the action (default from the rule)")
    s.add_argument("--provisional", action="store_true", help="reply inside a provisional (1.17(u) fees)")
    sub("provisional", "12-month nonprovisional / PCT date from a provisional", "filed")
    sub("bar", "US grace-period last day after a disclosure", "disclosed")
    sub("pct", "30 and 31 months from priority", "priority")
    sub("maintenance", "maintenance windows (3.5 / 7.5 / 11.5 years)", "grant-date")
    sub("issue-fee", "issue fee date (3 months, not extendable)", "mailed")
    sub("reissue-broadening", "2-year broadening reissue date", "grant-date")
    sub("pgr", "9-month PGR petition window", "grant-date")
    s = sub("ipr", "IPR earliest date and 315(b) bar", "grant-date")
    s.add_argument("--complaint-served", default=None)
    sub("damages-window", "35 USC 286 six-year look-back", "filed")
    s = sub("portfolio", "docket from portfolio.json events")
    s.add_argument("--file", default=None, help="portfolio.json path (default <dir>/portfolio.json)")
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
