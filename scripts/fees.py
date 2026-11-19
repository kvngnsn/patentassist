#!/usr/bin/env python3
"""USPTO utility fee estimates from references/fees.md (large / small / micro entity).

Every dollar amount comes from the "Machine-readable fees" json block in
references/fees.md, parsed at run time. Nothing is hardcoded here. Every result
prints the table's last_verified date: verify on the uspto.gov fee schedule before paying.

Examples:
    python3 scripts/fees.py estimate --type nonprovisional --entity small --claims patent/draft/claims.md --pages 38
    python3 scripts/fees.py estimate --type nonprovisional --entity small --independent 4 --total 25 --pages 120
    python3 scripts/fees.py estimate --type provisional --entity small --claims draft/claims.md --out draft/out
        (--out writes fees.md + fees.json there; a relative --out is under --dir; check_package.py reads
         the claim counts in fees.json for FEE_COUNTS)
    python3 scripts/fees.py --type provisional --entity micro --pages 140      (estimate is the default command)
    python3 scripts/fees.py issue --entity small
    python3 scripts/fees.py maintenance --grant-date 2022-03-08 --entity small
    python3 scripts/fees.py extension --months 2 --entity large
    python3 scripts/fees.py rce --entity small [--subsequent]
    python3 scripts/fees.py appeal --entity micro [--hearing]

Page counting (references/fees.md, "Size fee counting"; 37 CFR 1.52(f); MPEP 607):
    --pages N           sheets of spec + claims + abstract + drawings as Patent Center renders them.
                        E-filed (default): counted sheets = 75% of N, rounded UP (USPTO rounding is
                        unconfirmed; rounding up never under-estimates). --paper: counted = N.
    --counted-sheets N  the already-adjusted count, used as is.
    Size fee = each 50 sheets or fraction over 100 counted sheets (1.16(s)).

Exit codes: 0 ok, 2 usage or input error.
"""

import argparse
import datetime as _dt
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _dates import add_months, parse_date  # noqa: E402
from state import UsageError, add_common, audit, cli_main, finalize, new_result, to_namespace  # noqa: E402

SCRIPT = "fees.py"
FEES_MD = os.path.join(os.path.dirname(HERE), "references", "fees.md")
ENTITIES = ("large", "small", "micro")
VERIFY_LINE = "Verify on uspto.gov fee schedule before paying; table last verified %s."

_TABLE_CACHE = {}


# --------------------------------------------------------------------------- fee table


def load_fee_table(path=None):
    """Return the parsed json object {"fees": {...}, "thresholds": {...}} from fees.md.

    Looks for the fenced ```json block under "## Machine-readable fees"; falls back to the
    first json block that has a "fees" object."""
    path = path or FEES_MD
    if path in _TABLE_CACHE:
        return _TABLE_CACHE[path]
    if not os.path.exists(path):
        raise UsageError("fee table not found: %s" % path)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    start = text.find("## Machine-readable fees")
    blocks = []
    for m in re.finditer(r"```json[^\n]*\n(.*?)```", text, re.S):
        blocks.append((m.start() >= start >= 0, m.group(1)))
    blocks.sort(key=lambda b: not b[0])
    for _, body in blocks:
        try:
            obj = json.loads(body)
        except ValueError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("fees"), dict):
            fm = re.search(r"^last_verified:\s*(\S+)", text, re.M)
            meta = obj["fees"].get("_meta", {})
            obj["last_verified"] = meta.get("last_verified") or (fm.group(1) if fm else "unknown")
            obj["source_path"] = path
            _TABLE_CACHE[path] = obj
            return obj
    raise UsageError("no machine-readable fee json block found in %s" % path)


def fee_row(table, key):
    row = table["fees"].get(key)
    if not isinstance(row, dict):
        raise UsageError("fee %r is not in references/fees.md" % key)
    return row


def amount(table, key, entity):
    """Dollar amount for one entity, or None when the table lists no such fee."""
    v = fee_row(table, key).get(entity)
    return v if isinstance(v, (int, float)) else None


def amounts(table, key):
    row = fee_row(table, key)
    return {e: row.get(e) for e in ENTITIES}


def extension_key(months, provisional=False):
    months = int(months)
    if not 1 <= months <= 5:
        raise UsageError("extension months must be 1-5 (37 CFR 1.136(a)); got %d" % months)
    base = "provisional_extension_" if provisional else "extension_"
    return base + ("1_month" if months == 1 else "%d_months" % months)


def threshold(table, name, default=None):
    return table.get("thresholds", {}).get(name, default)


def verify_line(table):
    return VERIFY_LINE % table.get("last_verified", "unknown")


def money(v):
    if v is None:
        return "n/a"
    if isinstance(v, float) and not v.is_integer():
        return "${:,.2f}".format(v)
    return "${:,}".format(int(v))


# --------------------------------------------------------------------------- items


def _item(table, key, entity, count=1, name=None, note=None, unit_override=None):
    row = fee_row(table, key)
    unit = unit_override if unit_override is not None else amount(table, key, entity)
    codes = row.get("codes") or [None, None, None]
    code = codes[ENTITIES.index(entity)] if len(codes) == 3 else None
    return {"key": key, "fee": name or key.replace("_", " "), "cfr": row.get("cfr"), "code": code,
            "unit": unit, "count": count, "subtotal": (unit or 0) * count,
            "by_entity": amounts(table, key), "note": note}


def _table_lines(items, entity, total):
    w = max([len(i["fee"]) for i in items] + [10])
    lines = ["%-*s  %-14s  %10s  %5s  %10s" % (w, "Fee", "37 CFR", entity.capitalize(), "Count", "Subtotal"),
             "%s  %s  %s  %s  %s" % ("-" * w, "-" * 14, "-" * 10, "-" * 5, "-" * 10)]
    for i in items:
        lines.append("%-*s  %-14s  %10s  %5s  %10s" % (w, i["fee"], i["cfr"] or "", money(i["unit"]),
                                                       i["count"], money(i["subtotal"])))
        if i.get("note"):
            lines.append("%-*s    (%s)" % (w, "", i["note"]))
    lines.append("%-*s  %-14s  %10s  %5s  %10s" % (w, "TOTAL", "", "", "", money(total)))
    return lines


# --------------------------------------------------------------------------- claim counting


def _minimal_parse(text):
    """Fallback claim parser: number at line start begins a claim; dependency from 'claim N'."""
    claims, cur = [], None
    for raw in text.splitlines():
        line = re.sub(r"(\*\*|__)", "", raw.rstrip())
        m = re.match(r"^\s{0,3}(\d+)\s*[.)]\s*(.*)$", line)
        if m:
            cur = {"num": int(m.group(1)), "text": m.group(2).strip()}
            claims.append(cur)
        elif cur is not None and line.strip() and not line.strip().startswith("#"):
            cur["text"] += " " + line.strip()
    out = []
    for c in claims:
        t = c["text"]
        if re.match(r"^\(\s*(canceled|cancelled|not entered)\s*\)", t, re.I):
            continue
        refs = []
        for m in re.finditer(r"\bclaims?\s+((?:\d+\s*(?:,|or|and|to|through|-|–)?\s*)+)", t, re.I):
            seg = m.group(1)
            for a, b in re.findall(r"(\d+)\s*(?:-|–|to|through)\s*(\d+)", seg):
                refs.extend(range(int(a), int(b) + 1))
            refs.extend(int(x) for x in re.findall(r"\d+", re.sub(r"\d+\s*(?:-|–|to|through)\s*\d+", "", seg)))
        refs = sorted(set(r for r in refs if r < c["num"]))
        kind = "independent" if not refs else ("single" if len(refs) == 1 else "multiple")
        out.append({"num": c["num"], "deps": refs, "dep_kind": kind})
    by_num = {c["num"]: c for c in out}
    weights = {}

    def weight(c, depth=0):
        if c["num"] in weights or depth > 50:
            return weights.get(c["num"], 1)
        if c["dep_kind"] == "independent":
            w = 1
        elif c["dep_kind"] == "multiple":
            w = len([d for d in c["deps"] if d in by_num])  # 37 CFR 1.75(c)
        else:
            p = by_num.get(c["deps"][0])
            w = weight(p, depth + 1) if p is not None else 1  # inherits an MD parent's count
        weights[c["num"]] = max(1, w)
        return weights[c["num"]]

    total = sum(weight(c) for c in out)
    return {"independent": len([c for c in out if c["dep_kind"] == "independent"]),
            "total_for_fees": total, "multiple_dependent": [c["num"] for c in out if c["dep_kind"] == "multiple"],
            "parser": "fees.py minimal parser"}


def count_claims_file(path):
    """Counts for fees: uses scripts/check_claims.py when present, else a minimal parser."""
    if not os.path.exists(path):
        raise UsageError("claims file not found: %s" % path)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    try:
        import check_claims  # noqa: WPS433 (written by another agent; optional)
        claims = check_claims.parse_claims(text)
        c = check_claims.fee_counts(claims)
        return {"independent": int(c["independent"]), "total_for_fees": int(c["total_for_fees"]),
                "multiple_dependent": list(c.get("multiple_dependent") or []), "parser": "check_claims.py"}
    except ImportError:
        return _minimal_parse(text)
    except Exception as e:  # parser changed shape: fall back, and say so
        r = _minimal_parse(text)
        r["parser"] += " (check_claims.py failed: %s)" % e.__class__.__name__
        return r


# --------------------------------------------------------------------------- estimate


def size_units(counted_sheets, table):
    free = threshold(table, "free_sheets", 100)
    per = threshold(table, "sheets_per_size_unit", 50)
    if counted_sheets is None or counted_sheets <= free:
        return 0
    return int(math.ceil((counted_sheets - free) / float(per)))


def counted_sheets_from(a, table, caveats):
    if a.counted_sheets is not None:
        return int(a.counted_sheets), "given as counted sheets"
    if a.pages is None:
        return None, None
    pages = int(a.pages)
    if a.paper:
        return pages, "paper filing: every sheet counts"
    factor = threshold(table, "efiled_sheet_factor", 0.75)
    exact = pages * factor
    counted = int(math.ceil(exact - 1e-9))
    free = threshold(table, "free_sheets", 100)
    how = "e-filed: %d rendered sheets x %s = %s, rounded up to %d (37 CFR 1.52(f); MPEP 607)" % (
        pages, factor, ("%g" % exact), counted)
    if exact != counted:
        lo = int(math.floor(exact))
        if size_units(lo, table) != size_units(counted, table):
            caveats.append("Rounding matters here: %g sheets is %d rounded down but %d rounded up, which changes "
                           "the size fee. USPTO rounding of the 75%% figure is unconfirmed (fees.md)." % (exact, lo, counted))
    if counted <= free < pages:
        caveats.append("%d rendered sheets exceed %d, but after the 75%% e-filing adjustment only %d count "
                       "(no size fee unless filed on paper)." % (pages, free, counted))
    return counted, how


def _claim_counts(a, caveats):
    if a.claims:
        c = count_claims_file(a.claims)
        caveats.append("Claim counts from %s (%s): %d independent, %d total for fees%s." % (
            a.claims, c["parser"], c["independent"], c["total_for_fees"],
            (", multiple dependent claim(s) %s" % ", ".join(str(x) for x in c["multiple_dependent"]))
            if c["multiple_dependent"] else ""))
        return c["independent"], c["total_for_fees"], len(c["multiple_dependent"]), c["parser"]
    if a.independent is None and a.total is None and a.multiple_dependent is None:
        return None, None, 0, None
    indep = int(a.independent or 0)
    total = int(a.total if a.total is not None else indep)
    md = int(a.multiple_dependent or 0)
    if total < indep:
        raise UsageError("--total (%d) is smaller than --independent (%d)" % (total, indep))
    if md:
        caveats.append("With --multiple-dependent, --total must already count each multiple dependent claim as the "
                       "number of claims it refers to, and each claim depending from it the same way (37 CFR 1.75(c)).")
    return indep, total, md, "given"


def _continuing(a, table, entity, items, caveats):
    if not a.continuing:
        return
    if a.type != "nonprovisional":
        caveats.append("--continuing ignored: 1.17(w) applies to nonprovisional applications only.")
        return
    if not a.earliest_benefit:
        r1, r2 = amounts(table, "continuing_6_to_9y"), amounts(table, "continuing_over_9y")
        caveats.append("Continuing application: a 1.17(w) fee applies if filed more than 6 years after the earliest "
                       "benefit date (%s %s if 6-9 years; %s if over 9 years). Pass --earliest-benefit YYYY-MM-DD "
                       "to compute it. A claim only to a provisional (119(e)) does not trigger it."
                       % (entity, money(r1[entity]), money(r2[entity])))
        return
    benefit = parse_date(a.earliest_benefit)
    filed = parse_date(a.filing_date) if a.filing_date else _dt.date.today()
    six, nine = add_months(benefit, 72), add_months(benefit, 108)
    if filed > nine:
        items.append(_item(table, "continuing_over_9y", entity, name="Continuing application surcharge (over 9 years)",
                           note="earliest benefit %s, filing %s; less any 1.17(w)(1) already paid"
                           % (benefit.isoformat(), filed.isoformat())))
    elif filed > six:
        items.append(_item(table, "continuing_6_to_9y", entity, name="Continuing application surcharge (6-9 years)",
                           note="earliest benefit %s, filing %s" % (benefit.isoformat(), filed.isoformat())))
    else:
        caveats.append("Continuing application filed %s is not more than 6 years after the earliest benefit date %s: "
                       "no 1.17(w) fee (fee would start for filings after %s)."
                       % (filed.isoformat(), benefit.isoformat(), six.isoformat()))


def _ids(a, table, entity, items, caveats):
    if a.ids is None:
        return
    n = int(a.ids)
    tiers = threshold(table, "ids_size_tiers", [50, 100, 200])
    keys = ["ids_size_over_50", "ids_size_over_100", "ids_size_over_200"]
    due_key = None
    for t, k in zip(tiers, keys):
        if n > t:
            due_key = k
    paid = int(a.ids_size_paid or 0)
    if due_key:
        full = amount(table, due_key, entity)
        unit = max(0, (full or 0) - paid)
        items.append(_item(table, due_key, entity, name="IDS size fee (%d cumulative items)" % n, unit_override=unit,
                           note=("tier amount %s less %s already paid" % (money(full), money(paid))) if paid else
                           "cumulative tier; no entity discount"))
    else:
        caveats.append("IDS: %d cumulative items is not over %d, so no IDS size fee (1.17(v))." % (n, tiers[0]))
    timing = (a.ids_timing or "b").lower()
    if timing in ("c", "d"):
        items.append(_item(table, "ids_fee", entity, name="IDS fee (1.97(%s) timing)" % timing,
                           note="1.97(c): statement OR fee; 1.97(d): statement AND fee" if timing == "c" else
                           "1.97(d): 1.97(e) statement also required"))
    caveats.append("IDS size fee counts every item listed, including duplicates, for the life of the application; "
                   "every IDS needs the 1.98(a)(4) size-fee assertion.")


def estimate(a):
    table = load_fee_table(a.fees_file)
    entity = a.entity
    if entity not in ENTITIES:
        raise UsageError("--entity must be large, small, or micro")
    if a.type not in ("provisional", "nonprovisional", "national_stage"):
        raise UsageError("--type must be provisional, nonprovisional, or national_stage")
    if a.type == "national_stage":
        raise UsageError("National stage (35 USC 371) fees are set by 37 CFR 1.492 and are not in references/fees.md's "
                         "machine-readable table, so no estimate is given. Use the uspto.gov fee schedule "
                         "(PCT national stage section).")
    items, caveats = [], []
    docx = (a.docx or "yes").lower()
    if docx not in ("yes", "no"):
        raise UsageError("--docx must be yes or no")

    counted, how = counted_sheets_from(a, table, caveats)
    if how:
        caveats.append("Size fee page count: %s." % how)
    else:
        caveats.append("No --pages given: size fee not estimated (due if counted sheets exceed %d)."
                       % threshold(table, "free_sheets", 100))
    units = size_units(counted, table)

    if a.type == "provisional":
        items.append(_item(table, "provisional_filing", entity, name="Provisional filing fee"))
        if units:
            items.append(_item(table, "provisional_size_fee", entity, count=units,
                               name="Provisional size fee", note="%d counted sheets: %d unit(s) of 50 over 100"
                               % (counted, units)))
        if a.late_fee or a.late_declaration:
            items.append(_item(table, "provisional_late_surcharge", entity,
                               name="Surcharge: late provisional filing fee or cover sheet"))
        if a.late_declaration:
            caveats.append("A provisional needs no inventor declaration; --late-declaration was read as a late "
                           "filing fee or cover sheet (1.16(g)).")
        if a.extension_months:
            items.append(_item(table, extension_key(a.extension_months, provisional=True), entity,
                               name="Provisional extension of time, %d month(s)" % int(a.extension_months),
                               note="for a reply inside the provisional (e.g., missing parts); the 12-month date "
                                    "itself cannot be extended"))
        if any([a.independent, a.total, a.multiple_dependent, a.claims]):
            caveats.append("Provisional applications pay no claim fees; claim counts ignored.")
        if docx == "no":
            caveats.append("Non-DOCX surcharge does not apply to provisional applications (1.16(u)).")
        if a.ids is not None:
            caveats.append("No IDS is filed in a provisional; --ids ignored.")
        if a.track_one:
            caveats.append("Track One is not available for provisional applications (1.102(e)).")
    else:
        if a.paper:
            items.append(_item(table, "utility_basic_filing", entity, name="Basic filing fee, utility (paper)"))
            items.append(_item(table, "non_electronic_filing", entity, name="Non-electronic (paper) filing fee",
                               note="micro pays the small amount" if entity == "micro" else None))
        elif entity == "small" and amount(table, "utility_basic_filing_efiled", "small") is not None:
            items.append(_item(table, "utility_basic_filing_efiled", entity,
                               name="Basic filing fee, utility (small, e-filed)", note="fee code 4011, Patent Center"))
        else:
            items.append(_item(table, "utility_basic_filing", entity, name="Basic filing fee, utility"))
        items.append(_item(table, "utility_search", entity, name="Utility search fee"))
        items.append(_item(table, "utility_examination", entity, name="Utility examination fee"))

        indep, total, md, src = _claim_counts(a, caveats)
        if indep is None:
            caveats.append("No claim counts given (--claims or --independent/--total): excess claim fees not estimated.")
        else:
            fi = threshold(table, "free_independent_claims", 3)
            ft = threshold(table, "free_total_claims", 20)
            if indep > fi:
                items.append(_item(table, "excess_independent_claim", entity, count=indep - fi,
                                   name="Independent claims over %d" % fi, note="%d independent" % indep))
            if total > ft:
                items.append(_item(table, "excess_total_claim", entity, count=total - ft,
                                   name="Claims over %d" % ft, note="%d total for fees" % total))
            if md:
                items.append(_item(table, "multiple_dependent_claim", entity, name="Multiple dependent claim fee",
                                   note="once per application"))
            if a.track_one:
                bad = []
                if indep > threshold(table, "track_one_max_independent", 4):
                    bad.append("more than %d independent claims" % threshold(table, "track_one_max_independent", 4))
                if total > threshold(table, "track_one_max_total", 30):
                    bad.append("more than %d total claims" % threshold(table, "track_one_max_total", 30))
                if md and not threshold(table, "track_one_multiple_dependent_allowed", False):
                    bad.append("a multiple dependent claim")
                if bad:
                    caveats.append("Track One NOT available as claimed: %s (1.102(e))." % "; ".join(bad))
        if units:
            items.append(_item(table, "utility_size_fee", entity, count=units, name="Application size fee",
                               note="%d counted sheets: %d unit(s) of 50 over 100" % (counted, units)))
        if docx == "no" or a.paper:
            items.append(_item(table, "non_docx_surcharge", entity, name="Non-DOCX surcharge",
                               note="spec, claims or abstract not in DOCX" +
                               ("; applying it to paper filings is assumed (unconfirmed)" if a.paper else "")))
        if a.late_declaration or a.late_fee:
            items.append(_item(table, "late_filing_surcharge", entity,
                               name="Surcharge: late fee or late inventor's oath/declaration",
                               note="once; due within the missing-parts period (MPEP 601.01(a))"))
        if a.extension_months:
            items.append(_item(table, extension_key(a.extension_months), entity,
                               name="Extension of time, %d month(s)" % int(a.extension_months)))
        _continuing(a, table, entity, items, caveats)
        _ids(a, table, entity, items, caveats)
        if a.track_one:
            items.append(_item(table, "track_one_request", entity, name="Track One request"))
            items.append(_item(table, "processing_fee", entity, name="Track One processing fee"))
        caveats.append("Excess-claim fees are also due when claims are added later (1.16(h), (i)); a multiple dependent "
                       "claim counts as the number of claims it refers to (1.75(c)).")
        if not a.continuing:
            caveats.append("If this application claims benefit under 120/121/365(c)/386(c), pass --continuing: a 1.17(w) "
                           "fee may apply.")
        if not a.paper and docx == "yes":
            caveats.append("Assumes Patent Center filing with spec, claims and abstract in DOCX (no 1.16(u) surcharge).")
    total = sum(i["subtotal"] for i in items)
    if entity != "large":
        caveats.append("%s entity status must be true on the payment date (1.27 / 1.29); re-check before each fee."
                       % entity.capitalize())
    return {"type": a.type, "entity": entity, "items": items, "total": total, "counted_sheets": counted,
            "caveats": caveats, "table": table}


# --------------------------------------------------------------------------- other commands


def cmd_estimate(a, res):
    est = estimate(a)
    table = est.pop("table")
    res["estimate"] = {k: v for k, v in est.items()}
    res["last_verified"] = table["last_verified"]
    res["text"].append("Fee estimate: %s, %s entity" % (a.type, a.entity))
    res["text"].extend(_table_lines(est["items"], a.entity, est["total"]))
    if est["caveats"]:
        res["text"].append("Caveats:")
        res["text"].extend("  - " + c for c in est["caveats"])
    res["summary"] = {"total": est["total"], "entity": a.entity, "type": a.type}
    if a.out:
        written = write_fee_sheet(a, res, est, table)
        res["written"] = written
        res["text"].append("Wrote: %s" % ", ".join(written))


def _out_dir(a):
    out = a.out
    if os.path.isabs(out):
        return out
    d = a.dir or "patent"
    norm = os.path.normpath(out)
    if os.path.isdir(d) and not (norm == os.path.normpath(d) or norm.startswith(os.path.normpath(d) + os.sep)):
        return os.path.join(d, out)
    return out


def write_fee_sheet(a, res, est, table):
    """--out DIR: fees.md (the printed estimate) and fees.json (items, total, claim counts) where
    check_package.py looks for a fee sheet (draft/out/)."""
    import hashlib
    out = _out_dir(a)
    os.makedirs(out, exist_ok=True)
    counts = None
    if a.claims:
        c = count_claims_file(a.claims)
        counts = {"independent": c["independent"], "total_for_fees": c["total_for_fees"],
                  "multiple_dependent": c["multiple_dependent"], "parser": c["parser"], "claims_file": a.claims,
                  "claim_fees_apply": a.type != "provisional"}
    elif a.independent is not None or a.total is not None:
        indep = int(a.independent or 0)
        counts = {"independent": indep, "total_for_fees": int(a.total if a.total is not None else indep),
                  "multiple_dependent": int(a.multiple_dependent or 0), "parser": "given",
                  "claim_fees_apply": a.type != "provisional"}
    obj = {"schema": "patentassist/fees@1", "generated": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
           "type": a.type, "entity": a.entity, "items": est["items"], "total": est["total"],
           "counted_sheets": est.get("counted_sheets"), "claim_counts": counts, "caveats": est["caveats"],
           "last_verified": table["last_verified"], "verify": verify_line(table)}
    jp = os.path.join(out, "fees.json")
    with open(jp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    md = ["# Fee estimate (fees.py)", "",
          "Generated %s. %s" % (obj["generated"][:10], verify_line(table)), ""]
    if counts:
        md.append("Claim counts: %d independent, %d total for fees%s." % (
            counts["independent"], counts["total_for_fees"],
            "" if counts["claim_fees_apply"] else " (a provisional pays no claim fees)"))
        md.append("")
    md += ["```"] + [ln for ln in res["text"] if not ln.startswith("Wrote:")] + ["```", ""]
    mp = os.path.join(out, "fees.md")
    with open(mp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    for p in (mp, jp):
        if not a.no_audit and os.path.isdir(a.dir or ""):
            with open(p, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            audit(a.dir, "export", path=os.path.relpath(p, a.dir), sha256=digest, script=SCRIPT)
    return [mp, jp]


def _simple(a, res, title, specs, extra_caveats=()):
    table = load_fee_table(a.fees_file)
    entity = a.entity or "small"
    items = [_item(table, k, entity, name=n, note=note) for k, n, note in specs]
    total = sum(i["subtotal"] for i in items)
    res["estimate"] = {"entity": entity, "items": items, "total": total, "caveats": list(extra_caveats)}
    res["last_verified"] = table["last_verified"]
    res["text"].append("%s, %s entity%s" % (title, entity, "" if a.entity else " (default; pass --entity)"))
    res["text"].extend(_table_lines(items, entity, total))
    res["text"].append("All entities: " + "; ".join(
        "%s: %s" % (i["fee"], " / ".join("%s %s" % (e, money(i["by_entity"][e])) for e in ENTITIES)) for i in items))
    for c in extra_caveats:
        res["text"].append("  - " + c)
    res["summary"] = {"total": total, "entity": entity}
    return table


def cmd_issue(a, res):
    _simple(a, res, "Issue fee", [("utility_issue", "Utility issue fee", None),
                                  ("publication", "Publication fee", "now $0")],
            ["Due 3 months from the Notice of Allowance; not extendable (37 CFR 1.311). "
             "Run deadlines.py issue-fee --mailed D for the date."])


def cmd_extension(a, res):
    if a.months is None:
        raise UsageError("give --months N (1-5)")
    key = extension_key(a.months, provisional=a.provisional)
    table = _simple(a, res, "Extension of time (%s)" % ("provisional, 1.17(u)" if a.provisional else "1.136(a)"),
                    [(key, "Extension, %d month(s)" % int(a.months), "fee set by the month the reply is filed")],
                    ["No reply may go past the 6-month statutory limit (35 USC 133; 1.136(a))."])
    res["text"].append("Full ladder: " + "; ".join(
        "%d mo %s" % (n, money(amount(table, extension_key(n, a.provisional), a.entity or "small"))) for n in range(1, 6)))


def cmd_rce(a, res):
    key = "rce_subsequent" if a.subsequent else "rce_first"
    _simple(a, res, "Request for continued examination", [(key, "RCE, %s request" % ("second or later" if a.subsequent
                                                                                     else "first"), None)],
            ["An RCE needs a submission (reply/amendment) with it (37 CFR 1.114)."])


def cmd_appeal(a, res):
    specs = [("notice_of_appeal", "Notice of appeal", "with the reply period"),
             ("appeal_brief", "Appeal brief", "2 months from the notice (41.37)"),
             ("appeal_forwarding", "Appeal forwarding fee", "2 months from the examiner's answer (41.45)")]
    if a.hearing:
        specs.append(("oral_hearing", "Request for oral hearing", None))
    _simple(a, res, "Ex parte appeal", specs,
            ["Forwarding fee is paid only if the appeal goes forward after the examiner's answer."])


def maintenance_schedule(grant_date, entity, table, today=None):
    """Three maintenance stages: windows from deadlines.md rules, fees from fees.md."""
    import deadlines  # lazy: deadlines imports this module too
    out = []
    for stage, rid, fkey in ((1, "maintenance_1", "maintenance_3_5y"), (2, "maintenance_2", "maintenance_7_5y"),
                             (3, "maintenance_3", "maintenance_11_5y")):
        w = deadlines.maintenance_window(grant_date, rid, today=today)
        w.update({"stage": stage, "fee_key": fkey, "fee": amounts(table, fkey),
                  "surcharge": amounts(table, "maintenance_grace_surcharge"),
                  "fee_cfr": fee_row(table, fkey).get("cfr"),
                  "surcharge_cfr": fee_row(table, "maintenance_grace_surcharge").get("cfr")})
        if entity:
            w["entity_fee"] = amount(table, fkey, entity)
            w["entity_fee_with_surcharge"] = (w["entity_fee"] or 0) + (amount(table, "maintenance_grace_surcharge",
                                                                                entity) or 0)
        out.append(w)
    return out


def cmd_maintenance(a, res):
    if not a.grant_date:
        raise UsageError("give --grant-date YYYY-MM-DD")
    table = load_fee_table(a.fees_file)
    sched = maintenance_schedule(parse_date(a.grant_date), a.entity, table, a.today)
    res["maintenance"] = sched
    res["last_verified"] = table["last_verified"]
    res["text"].append("Maintenance fees, grant date %s%s" % (a.grant_date, (", %s entity" % a.entity) if a.entity else ""))
    for w in sched:
        fee = w["fee"]
        sur = w["surcharge"]
        res["text"].append("  Stage %d (%s, %s): window opens %s; last day without surcharge %s%s; grace (with "
                           "surcharge) through %s%s; status: %s" % (
                               w["stage"], w["label"], w["fee_cfr"], w["window_open"], w["due"],
                               (" (rolled from %s)" % w["due_unrolled"]) if w["due_rolled"] else "",
                               w["grace_end"], (" (rolled from %s)" % w["grace_end_unrolled"]) if w["grace_rolled"] else "",
                               w["status"]))
        res["text"].append("      fee large %s / small %s / micro %s; surcharge in grace (%s) large %s / small %s / micro %s"
                           % (money(fee["large"]), money(fee["small"]), money(fee["micro"]), w["surcharge_cfr"],
                              money(sur["large"]), money(sur["small"]), money(sur["micro"])))
    res["text"].append("  Unpaid after grace: the patent expires at the end of the 4th/8th/12th anniversary (1.362(g)); "
                       "delayed-payment petition under 1.378 (1.17(m)).")
    res["summary"] = {"grant_date": a.grant_date}


COMMANDS = {"estimate": cmd_estimate, "issue": cmd_issue, "maintenance": cmd_maintenance,
            "extension": cmd_extension, "rce": cmd_rce, "appeal": cmd_appeal}

DEFAULTS = {"command": "estimate", "dir": "patent", "json": False, "no_audit": True, "fees_file": None,
            "type": None, "entity": None, "claims": None, "independent": None, "total": None,
            "multiple_dependent": None, "pages": None, "counted_sheets": None, "paper": False, "ids": None,
            "ids_size_paid": 0, "ids_timing": "b", "docx": "yes", "late_declaration": False, "late_fee": False,
            "extension_months": None, "continuing": False, "earliest_benefit": None, "filing_date": None,
            "track_one": False, "months": None, "provisional": False, "subsequent": False, "hearing": False,
            "grant_date": None, "today": None, "out": None}


def run(args):
    a = to_namespace(args, DEFAULTS)
    if a.command is None:
        a.command = "estimate"
    if a.command not in COMMANDS:
        raise UsageError("command must be one of %s" % ", ".join(COMMANDS))
    if a.entity is not None and a.entity not in ENTITIES:
        raise UsageError("--entity must be large, small, or micro")
    if a.command == "estimate" and (not a.type or not a.entity):
        raise UsageError("estimate needs --type and --entity")
    res = new_result()
    res["command"] = a.command
    COMMANDS[a.command](a, res)
    res["verify"] = verify_line(load_fee_table(a.fees_file))
    res["text"].append(res["verify"])
    res["checks_run"].append("fees:%s" % a.command)
    return finalize(res)


def build_parser():
    p = argparse.ArgumentParser(prog="fees.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    add_common(p)
    p.add_argument("--fees-file", default=None, help=argparse.SUPPRESS)
    p.add_argument("--today", default=None, help=argparse.SUPPRESS)
    sp = p.add_subparsers(dest="command")

    def sub(name, help_):
        s = sp.add_parser(name, help=help_)
        add_common(s, sub=True)
        s.add_argument("--entity", choices=ENTITIES, default=None)
        s.add_argument("--fees-file", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        s.add_argument("--today", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
        return s

    s = sub("estimate", "filing fee estimate (provisional / nonprovisional)")
    s.add_argument("--type", required=True, choices=("provisional", "nonprovisional", "national_stage"))
    s.add_argument("--claims", default=None, help="claims.md to count (uses check_claims.py if present)")
    s.add_argument("--independent", type=int, default=None)
    s.add_argument("--total", type=int, default=None, help="total claims as counted for fees (1.75(c))")
    s.add_argument("--multiple-dependent", type=int, default=None, help="number of multiple dependent claims")
    s.add_argument("--pages", type=int, default=None, help="rendered sheets (spec+claims+abstract+drawings)")
    s.add_argument("--counted-sheets", type=int, default=None, help="sheets already adjusted for the size fee")
    s.add_argument("--paper", action="store_true", help="paper filing (no 75%% factor; paper fee; no 4011 code)")
    s.add_argument("--ids", type=int, default=None, help="cumulative IDS items listed")
    s.add_argument("--ids-size-paid", type=int, default=0, help="IDS size fees already paid ($)")
    s.add_argument("--ids-timing", choices=("b", "c", "d"), default="b", help="37 CFR 1.97 window (default b)")
    s.add_argument("--docx", choices=("yes", "no"), default="yes")
    s.add_argument("--late-declaration", action="store_true", help="declaration not filed with the application")
    s.add_argument("--late-fee", action="store_true", help="filing/search/exam fee (or cover sheet) paid late")
    s.add_argument("--extension-months", type=int, default=None)
    s.add_argument("--continuing", action="store_true", help="claims benefit under 120/121/365(c)/386(c)")
    s.add_argument("--earliest-benefit", default=None, help="earliest benefit date for 1.17(w)")
    s.add_argument("--filing-date", default=None, help="planned filing date for 1.17(w) (default today)")
    s.add_argument("--track-one", action="store_true", help="add Track One request + processing fee")
    s.add_argument("--out", default=None, help="write fees.md + fees.json into this folder (e.g. draft/out)")

    sub("issue", "utility issue fee")
    s = sub("maintenance", "maintenance fee windows and amounts")
    s.add_argument("--grant-date", required=True)
    s = sub("extension", "extension of time fee")
    s.add_argument("--months", type=int, required=True)
    s.add_argument("--provisional", action="store_true", help="provisional-application extension (1.17(u))")
    s = sub("rce", "RCE fee")
    s.add_argument("--subsequent", action="store_true", help="second or later RCE")
    s = sub("appeal", "appeal fees")
    s.add_argument("--hearing", action="store_true", help="include oral hearing fee")
    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].startswith("--") and argv[0] not in ("--help", "-h") and "--type" in argv \
            and not any(x in COMMANDS for x in argv):
        argv = ["estimate"] + argv  # phases/3-draft.md calls `fees.py --type ... --entity ...`
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
