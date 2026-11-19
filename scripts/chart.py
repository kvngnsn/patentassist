#!/usr/bin/env python3
"""Claim charts (patentassist/chart@1): render, validate, list needs-evidence, build from prior art.

    python3 scripts/chart.py render charts/X.json [--md] [--csv] [--docx] [--by reference|element] [--out BASE]
    python3 scripts/chart.py validate charts/X.json
    python3 scripts/chart.py needs-evidence charts/X.json
    python3 scripts/chart.py from-prior-art [--dir patent] [--out charts/patentability.json] [--refs R1,R2]
                                            [--categories X,Y] [--force]

Common options: --dir (default patent), --json, --no-audit.

Charts are leads, not contentions: every rendering carries a DRAFT banner, marks
construction-dependent cells with a dagger, shows each cell's pinpoint and quote, and
ends with the needs-evidence list and the 103-gaps list. CSV cells that start with
= + - @ tab or CR are prefixed with a single quote so a spreadsheet will not run them as
formulas.

needs-evidence lists only what still needs proof: unknown cells, inherent cells, construction-
dependent cells, positive cells missing a quote or pinpoint, and unverified references. Partial
cells are findings, not missing evidence: they go in a separate "103 gaps" list.

--by element prints one row per element with state + pinpoint only; quotes and analysis go in
numbered footnotes under the table. --by reference (default) prints one table per reference.

Relative paths: a relative --out is resolved under --dir (so `--out charts/x.json` writes
<dir>/charts/x.json), and a chart path that does not exist as given is looked up under --dir.

Machine translations: when a reference's cached record (cache/<NUMBER>.json) says its text is a
machine translation, or the chart ref has "machine_translation": true, every rendered cell for that
reference gets "[machine translation – review]".

Exit codes: 0 ok, 1 blocking findings (validate), 2 usage or input error.
"""

import argparse
import csv
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import (SCHEMA_CHART, SCHEMA_PRIOR_ART, UsageError, audit, check_schema, finding,  # noqa: E402
                   to_namespace, write_json)

SCRIPT = "chart.py"
KINDS = ("patentability", "invalidity", "infringement", "fto")
STATES = {
    "patentability": ("explicit", "inherent", "partial", "absent", "unknown"),
    "invalidity": ("explicit", "inherent", "partial", "absent", "unknown"),
    "infringement": ("literal", "doe", "partial", "absent", "unknown"),
    "fto": ("literal", "doe", "partial", "absent", "unknown"),
}
STATE_WORDS = {"explicit": "Explicit", "inherent": "Inherent", "partial": "Partial", "absent": "Absent",
               "unknown": "Unknown", "literal": "Literal", "doe": "DOE (equivalents)"}
POSITIVE = {"explicit", "inherent", "partial", "literal", "doe"}
BANNER = ("DRAFT - claim chart for review. Cells are leads, not legal conclusions or contentions; "
          "a person must check each cell against the source and tick \"verified\".")
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
MT_TAG = "[machine translation \u2013 review]"


# --------------------------------------------------------------------------- loading


def load_chart(path):
    if not path or not os.path.exists(path):
        raise UsageError("chart file not found: %s" % path)
    try:
        with open(path, encoding="utf-8") as fh:
            obj = json.load(fh)
    except ValueError as e:
        raise UsageError("%s is not valid JSON: %s" % (path, e))
    check_schema(obj, SCHEMA_CHART, path)
    return obj


def _el_map(chart):
    return {str(e.get("id")): e for e in chart.get("elements", []) or []}


def _ref_map(chart):
    return {str(r.get("id")): r for r in chart.get("refs", []) or []}


def _ref_label(r):
    if not r:
        return "?"
    lab = r.get("number") or r.get("label") or r.get("id")
    if r.get("verified") is False or r.get("ref_verified") is False:
        lab += " (UNVERIFIED)"
    return "%s: %s" % (r.get("id"), lab) if r.get("id") and r.get("id") != lab else lab


# --------------------------------------------------------------------------- validate / needs-evidence


def validate(chart):
    f = []
    kind = chart.get("kind")
    if kind not in KINDS:
        f.append(finding("BLOCK", "KIND", "chart", "kind %r is not one of %s" % (kind, ", ".join(KINDS))))
        allowed = set(s for v in STATES.values() for s in v)
    else:
        allowed = set(STATES[kind])
    els, refs = _el_map(chart), _ref_map(chart)
    if not els:
        f.append(finding("BLOCK", "ELEMENTS", "chart", "no elements"))
    if not refs:
        f.append(finding("WARN", "REFS", "chart", "no refs"))
    seen = set()
    covered = set()
    for i, c in enumerate(chart.get("cells", []) or []):
        where = "cell %d (%s x %s)" % (i + 1, c.get("element"), c.get("ref"))
        el, ref = str(c.get("element")), str(c.get("ref"))
        if el not in els:
            f.append(finding("BLOCK", "CELL_ELEMENT", where, "element %r is not in elements" % el))
        if ref not in refs:
            f.append(finding("BLOCK", "CELL_REF", where, "ref %r is not in refs" % ref))
        if (el, ref) in seen:
            f.append(finding("BLOCK", "CELL_DUP", where, "more than one cell for this element and ref"))
        seen.add((el, ref))
        covered.add(el)
        st = c.get("state")
        if st not in allowed:
            f.append(finding("BLOCK", "STATE", where, "state %r is not allowed in a %s chart (allowed: %s)"
                             % (st, kind, ", ".join(sorted(allowed)))))
        if st in POSITIVE and not (c.get("quote") or "").strip():
            f.append(finding("WARN", "QUOTE", where, "state %s has no verbatim quote" % st))
        if st in POSITIVE and not (c.get("pinpoint") or "").strip():
            f.append(finding("WARN", "PINPOINT", where, "state %s has no pinpoint" % st))
        if "verified" in c and not isinstance(c.get("verified"), bool):
            f.append(finding("BLOCK", "VERIFIED", where, "verified must be true or false"))
        if "construction_dependent" in c and not isinstance(c.get("construction_dependent"), bool):
            f.append(finding("WARN", "CONSTRUCTION", where, "construction_dependent should be true or false"))
    for el in els:
        if el not in covered:
            f.append(finding("WARN", "UNCHARTED", "element %s" % el, "no cell charts this element"))
    if chart.get("needs_evidence") is not None and not isinstance(chart.get("needs_evidence"), list):
        f.append(finding("WARN", "NEEDS_EVIDENCE", "chart", "needs_evidence should be a list"))
    return f


_PARTIAL_NOTE = re.compile(r"^\S+ vs \S+: partial\b")


def _cell_label(c, refs):
    return "%s vs %s" % (c.get("element"), (refs.get(str(c.get("ref"))) or {}).get("id", c.get("ref")))


def gaps_103(chart):
    """Partial cells: what each reference lacks for an element (findings for the 103 analysis)."""
    refs = _ref_map(chart)
    out = []
    for c in chart.get("cells", []) or []:
        if c.get("state") == "partial":
            out.append("%s: partial%s" % (_cell_label(c, refs),
                                          (" (%s)" % c["analysis"]) if c.get("analysis") else ""))
    return out


def needs_evidence(chart):
    """(list, unverified_cell_count). Lists unknown, inherent, construction-dependent, and positive cells
    without a quote or pinpoint, plus unverified references. Partial cells are in gaps_103()."""
    out = []
    els, refs = _el_map(chart), _ref_map(chart)
    for c in chart.get("cells", []) or []:
        st = c.get("state")
        label = _cell_label(c, refs)
        reasons = []
        if st == "unknown":
            reasons.append("state unknown (could not read enough)")
        if st == "inherent":
            reasons.append("inherent: needs evidence that the feature necessarily follows")
        if c.get("construction_dependent"):
            reasons.append("turns on claim construction")
        if st in POSITIVE and not (c.get("quote") or "").strip():
            reasons.append("no quote")
        if st in POSITIVE and not (c.get("pinpoint") or "").strip():
            reasons.append("no pinpoint")
        if reasons:
            out.append("%s: %s" % (label, "; ".join(reasons)))
    for r in refs.values():
        if r.get("verified") is False or r.get("ref_verified") is False:
            out.append("%s: reference not verified (UNVERIFIED)" % r.get("id"))
    keys = set(x.split(":", 1)[0].strip() for x in out)
    for n in chart.get("needs_evidence", []) or []:
        n = str(n)
        if _PARTIAL_NOTE.match(n):
            continue  # older charts stored partial cells here; they are 103 gaps now
        if n not in out and n.split(":", 1)[0].strip() not in keys:
            out.append(n)
    unver = sum(1 for c in chart.get("cells", []) or [] if not c.get("verified"))
    return out, unver


# --------------------------------------------------------------------------- rendering


def state_word(c):
    w = STATE_WORDS.get(c.get("state"), str(c.get("state") or "Unknown").title())
    return w + (" \u2020" if c.get("construction_dependent") else "")


def _md(s):
    return str(s if s is not None else "").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def _compact_cell(c, note_no=None, mt=False):
    """by-element cell: state + pinpoint (+ footnote number); quote and analysis go in the footnote."""
    s = "**%s**" % state_word(c)
    if c.get("pinpoint"):
        s += " \u2014 %s" % _md(c["pinpoint"])
    if note_no:
        s += " [%d]" % note_no
    if mt:
        s += " " + MT_TAG
    return s


def machine_translated_refs(chart, dirpath=None):
    """Ref ids whose text is a machine translation (chart flag, or the cached record's notes)."""
    out = set()
    find_cached = None
    if dirpath and os.path.isdir(os.path.join(dirpath, "cache")):
        try:
            from patent_fetch import find_cached
        except Exception:  # pragma: no cover - patent_fetch is part of this folder
            find_cached = None
    for rid, r in _ref_map(chart).items():
        if r.get("machine_translation"):
            out.add(rid)
            continue
        if find_cached and r.get("number"):
            try:
                _, rec = find_cached(dirpath, r["number"])
            except Exception:
                rec = None
            if rec and any("machine translation" in str(n).lower() for n in rec.get("notes") or []):
                out.add(rid)
    return out


def render_md(chart, by="reference", mt=None):
    mt = mt or set()
    els, refs = _el_map(chart), _ref_map(chart)
    cells = chart.get("cells", []) or []
    subj = chart.get("subject") or {}
    lines = ["> **%s**" % BANNER, ""]
    title = "%s chart" % (chart.get("kind") or "claim").title()
    if subj.get("label"):
        title += ": %s" % subj["label"]
    if subj.get("claim"):
        title += " (claim %s)" % subj["claim"]
    lines += ["# %s" % _md(title), ""]
    lines.append("States: %s. \u2020 = construction-dependent." % ", ".join(
        STATE_WORDS[s] for s in STATES.get(chart.get("kind"), STATES["patentability"])))
    lines.append("")
    if by == "element":
        ref_ids = list(refs)
        lines.append("| Element | " + " | ".join(_md(_ref_label(refs[r])) for r in ref_ids) + " |")
        lines.append("|---|" + "---|" * len(ref_ids))
        idx = {(str(c.get("element")), str(c.get("ref"))): c for c in cells}
        notes = []
        for eid, e in els.items():
            row = ["**%s** %s" % (_md(eid), _md(e.get("text")))]
            for r in ref_ids:
                c = idx.get((eid, r))
                if not c:
                    row.append("Unknown (not charted)")
                    continue
                n = None
                if c.get("quote") or c.get("analysis") or not c.get("verified"):
                    parts = ["%s \u00d7 %s%s:" % (_md(refs[r].get("id") or r), _md(eid),
                                                   (" (%s)" % _md(c["pinpoint"])) if c.get("pinpoint") else "")]
                    if c.get("quote"):
                        parts.append("\u201c%s\u201d" % _md(c["quote"]))
                    if c.get("analysis"):
                        parts.append("\u2014 %s" % _md(c["analysis"]))
                    if r in mt:
                        parts.append(MT_TAG)
                    if not c.get("verified"):
                        parts.append("_unverified_")
                    notes.append(" ".join(parts))
                    n = len(notes)
                row.append(_compact_cell(c, n, r in mt))
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
        if notes:
            lines.append("### Quotes and notes")
            lines.append("")
            lines.extend("[%d] %s  " % (i, t) for i, t in enumerate(notes, 1))
            lines.append("")
    else:
        for rid, r in refs.items():
            lines.append("## %s" % _md(_ref_label(r)))
            if r.get("title"):
                lines.append("")
                lines.append("_%s_" % _md(r["title"]))
            lines.append("")
            lines.append("| Element | State | Pinpoint | Quote | Analysis | Verified |")
            lines.append("|---|---|---|---|---|---|")
            rcells = {str(c.get("element")): c for c in cells if str(c.get("ref")) == rid}
            for eid, e in els.items():
                c = rcells.get(eid)
                if c is None:
                    lines.append("| **%s** %s | Unknown (not charted) |  |  |  | no |" % (_md(eid), _md(e.get("text"))))
                    continue
                quote = ("\u201c%s\u201d" % _md(c["quote"])) if c.get("quote") else ""
                if rid in mt:
                    quote = (quote + " " + MT_TAG).strip()
                lines.append("| **%s** %s | %s | %s | %s | %s | %s |" % (
                    _md(eid), _md(e.get("text")), state_word(c), _md(c.get("pinpoint")),
                    quote, _md(c.get("analysis")), "yes" if c.get("verified") else "no"))
            lines.append("")
    notes = [e for e in els.values() if e.get("construction_note")]
    if notes:
        lines.append("## Construction notes")
        lines.append("")
        for e in notes:
            lines.append("- **%s**: %s" % (_md(e.get("id")), _md(e.get("construction_note"))))
        lines.append("")
    ne, unver = needs_evidence(chart)
    lines.append("## Needs evidence")
    lines.append("")
    if ne:
        lines.extend("- %s" % _md(n) for n in ne)
    else:
        lines.append("- none listed")
    lines.append("")
    gaps = gaps_103(chart)
    lines.append("## 103 gaps (partial matches)")
    lines.append("")
    if gaps:
        lines.extend("- %s" % _md(n) for n in gaps)
    else:
        lines.append("- none")
    lines.append("")
    lines.append("%d of %d cells not yet verified by a person." % (unver, len(cells)))
    lines.append("")
    return "\n".join(lines)


def safe_csv(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    if s.startswith(FORMULA_START):
        return "'" + s
    return s


CSV_COLS = ["element", "element_text", "ref", "ref_number", "state", "construction_dependent", "pinpoint", "quote",
            "analysis", "verified", "machine_translation"]


def render_csv(chart, mt=None):
    mt = mt or set()
    els, refs = _el_map(chart), _ref_map(chart)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for c in chart.get("cells", []) or []:
        e = els.get(str(c.get("element"))) or {}
        r = refs.get(str(c.get("ref"))) or {}
        row = [c.get("element"), e.get("text"), c.get("ref"), r.get("number"), STATE_WORDS.get(c.get("state"),
               c.get("state")), bool(c.get("construction_dependent")), c.get("pinpoint"), c.get("quote"),
               c.get("analysis"), bool(c.get("verified")), str(c.get("ref")) in mt]
        w.writerow([safe_csv(x) for x in row])
    return buf.getvalue()


def render_docx(chart, out_path, by="reference", mt=None):
    mt = mt or set()
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.oxml.ns import qn
    except ImportError:
        raise UsageError("python-docx is required for --docx: pip install python-docx")
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for s in doc.sections:
        hp = s.header.paragraphs[0]
        hp.text = "DRAFT - claim chart for review"
    p = doc.add_paragraph()
    r = p.add_run(BANNER)
    r.bold = True
    r.font.color.rgb = RGBColor(0x99, 0x00, 0x00)
    subj = chart.get("subject") or {}
    doc.add_heading("%s chart%s" % ((chart.get("kind") or "claim").title(),
                                    (": " + subj["label"]) if subj.get("label") else ""), level=1)
    doc.add_paragraph("\u2020 = construction-dependent.")
    els, refs = _el_map(chart), _ref_map(chart)
    cells = chart.get("cells", []) or []
    for rid, ref in refs.items():
        doc.add_heading(_ref_label(ref), level=2)
        t = doc.add_table(rows=1, cols=6)
        t.style = "Table Grid"
        for i, h in enumerate(["Element", "State", "Pinpoint", "Quote", "Analysis", "Verified"]):
            t.rows[0].cells[i].text = h
            for run in t.rows[0].cells[i].paragraphs[0].runs:
                run.bold = True
        rcells = {str(c.get("element")): c for c in cells if str(c.get("ref")) == rid}
        for eid, e in els.items():
            c = rcells.get(eid) or {"state": "unknown"}
            row = t.add_row().cells
            row[0].text = "%s %s" % (eid, e.get("text") or "")
            row[1].text = state_word(c) + ("" if eid in rcells else " (not charted)")
            row[2].text = str(c.get("pinpoint") or "")
            row[3].text = (("\u201c%s\u201d" % c["quote"]) if c.get("quote") else "") + \
                ((" " + MT_TAG) if rid in mt and eid in rcells else "")
            row[4].text = str(c.get("analysis") or "")
            row[5].text = "yes" if c.get("verified") else "no"
    doc.add_heading("Needs evidence", level=2)
    ne, unver = needs_evidence(chart)
    for n in ne or ["none listed"]:
        doc.add_paragraph(n, style="List Bullet")
    doc.add_heading("103 gaps (partial matches)", level=2)
    for n in gaps_103(chart) or ["none"]:
        doc.add_paragraph(n, style="List Bullet")
    doc.add_paragraph("%d of %d cells not yet verified by a person." % (unver, len(cells)))
    doc.save(out_path)


# --------------------------------------------------------------------------- from-prior-art


def build_from_prior_art(pa, refs_filter=None, cats=None, label=None, previous=None):
    els = [{"id": str(e.get("id")), "text": e.get("text"), "construction_note": e.get("construction_note")}
           for e in pa.get("elements", []) or []]
    if not els:
        raise UsageError("prior-art.json has no elements")
    refs, cells, ne = [], [], []
    prev_ver = {}
    for c in (previous or {}).get("cells", []) or []:
        prev_ver[(str(c.get("element")), str(c.get("ref")), c.get("quote"), c.get("state"))] = bool(c.get("verified"))
    for r in pa.get("references", []) or []:
        rid = str(r.get("id"))
        if refs_filter and rid not in refs_filter:
            continue
        if cats and (r.get("category") or "") not in cats:
            continue
        em = r.get("element_map")
        if not isinstance(em, dict) or not em:
            continue
        cref = {"id": rid, "number": r.get("number") or r.get("title"), "title": r.get("title"),
                "verified": bool(r.get("verified")), "category": r.get("category")}
        if r.get("machine_translation"):
            cref["machine_translation"] = True
        refs.append(cref)
        if not r.get("verified"):
            ne.append("%s: reference not verified (UNVERIFIED)" % rid)
        for e in els:
            m = em.get(e["id"])
            if not isinstance(m, dict):
                cell = {"element": e["id"], "ref": rid, "state": "unknown", "construction_dependent": False,
                        "quote": None, "pinpoint": None, "analysis": "not mapped in prior-art.json", "verified": False}
            else:
                st = m.get("state") if m.get("state") in STATES["patentability"] else "unknown"
                cell = {"element": e["id"], "ref": rid, "state": st,
                        "construction_dependent": bool(m.get("construction_dependent")),
                        "quote": m.get("quote"), "pinpoint": m.get("pinpoint"),
                        "analysis": m.get("note") or m.get("analysis"), "verified": False}
            key = (cell["element"], rid, cell["quote"], cell["state"])
            if prev_ver.get(key):
                cell["verified"] = True  # keep a person's tick when the cell is unchanged
            cells.append(cell)
            if cell["state"] in ("unknown", "inherent") or cell["construction_dependent"]:
                why = ("unknown" if cell["state"] == "unknown" else "inherent" if cell["state"] == "inherent"
                       else "construction-dependent")
                ne.append("%s vs %s: %s%s" % (e["id"], rid, why,
                                              (" (%s)" % cell["analysis"]) if cell.get("analysis") else ""))
    if not refs:
        raise UsageError("no references with an element_map matched (check --refs / --categories)")
    return {"schema": SCHEMA_CHART, "kind": "patentability",
            "subject": {"type": "invention", "label": label, "claim": None},
            "elements": els, "refs": refs, "cells": cells, "needs_evidence": ne,
            "source": "prior-art.json (%s)" % (pa.get("stage") or "search")}


# --------------------------------------------------------------------------- run

DEFAULTS = {"command": None, "chart": None, "md": False, "csv": False, "docx": False, "by": "reference",
            "out": None, "dir": "patent", "json": False, "no_audit": False, "refs": None, "categories": None,
            "force": False}


def under_dir(path, dirpath):
    """A relative path is taken as relative to the matter folder (--dir), unless it already starts
    with that folder. Absolute paths are kept."""
    if not path or os.path.isabs(path) or not dirpath:
        return path
    np_, nd = os.path.normpath(path), os.path.normpath(dirpath)
    if nd in (".", "") or np_ == nd or np_.startswith(nd + os.sep):
        return path
    return os.path.join(dirpath, path)


def resolve_chart(path, dirpath):
    if path and not os.path.exists(path) and not os.path.isabs(path) and dirpath:
        alt = os.path.join(dirpath, path)
        if os.path.exists(alt):
            return alt
    return path


def _base_out(a):
    if a.out:
        out = under_dir(a.out, a.dir)
        return out[:-5] if out.endswith(".json") else os.path.splitext(out)[0] if \
            os.path.splitext(out)[1] in (".md", ".csv", ".docx") else out
    return os.path.splitext(a.chart)[0]


def run(args):
    a = to_namespace(args, DEFAULTS)
    res = {"ok": True, "exit_code": 0, "findings": [], "checks_run": [], "checks_skipped": [], "summary": {},
           "text": []}
    cmd = a.command
    if a.chart:
        a.chart = resolve_chart(a.chart, a.dir)
    if cmd == "validate":
        chart = load_chart(a.chart)
        f = validate(chart)
        res["findings"] = f
        res["checks_run"] = ["KIND", "STATES", "CELLS", "QUOTES", "COVERAGE"]
        blocks = sum(1 for x in f if x["level"] == "BLOCK")
        res["summary"] = {"blocking": blocks, "warnings": sum(1 for x in f if x["level"] == "WARN"),
                          "cells": len(chart.get("cells") or [])}
        res["exit_code"] = 1 if blocks else 0
        res["ok"] = not blocks
        audit(a.dir, "check", no_audit=a.no_audit or not os.path.isdir(a.dir), script=SCRIPT, file=a.chart,
              blocking=blocks, warnings=res["summary"]["warnings"])
        res["text"].append("chart.py validate  %s" % a.chart)
    elif cmd == "needs-evidence":
        chart = load_chart(a.chart)
        ne, unver = needs_evidence(chart)
        gaps = gaps_103(chart)
        res["needs_evidence"] = ne
        res["gaps_103"] = gaps
        res["summary"] = {"needs_evidence": len(ne), "gaps_103": len(gaps), "unverified_cells": unver,
                          "cells": len(chart.get("cells") or [])}
        res["text"].append("Needs evidence (%d):" % len(ne))
        res["text"].extend("  - %s" % n for n in ne)
        res["text"].append("103 gaps, partial matches (%d):" % len(gaps))
        res["text"].extend("  - %s" % n for n in gaps)
        res["text"].append("%d of %d cells not yet verified by a person." % (unver, len(chart.get("cells") or [])))
    elif cmd == "render":
        chart = load_chart(a.chart)
        bad = [x for x in validate(chart) if x["level"] == "BLOCK"]
        if bad:
            res["findings"] = bad
            res["exit_code"], res["ok"] = 1, False
            res["text"].append("chart has blocking problems; run `chart.py validate` and fix them first")
            return res
        want_md = a.md or not (a.csv or a.docx)
        base = _base_out(a)
        if os.path.dirname(base):
            os.makedirs(os.path.dirname(base), exist_ok=True)
        mt = machine_translated_refs(chart, a.dir)
        if mt:
            res["machine_translated_refs"] = sorted(mt)
            res["text"].append("machine translation (cells tagged %s): %s" % (MT_TAG, ", ".join(sorted(mt))))
        written = []
        if want_md:
            p = base + ".md"
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(render_md(chart, a.by, mt))
            written.append(p)
        if a.csv:
            p = base + ".csv"
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(render_csv(chart, mt))
            written.append(p)
        if a.docx:
            p = base + ".docx"
            render_docx(chart, p, a.by, mt)
            written.append(p)
        res["written"] = written
        res["text"].extend("wrote %s" % p for p in written)
        for p in written:
            audit(a.dir, "export", no_audit=a.no_audit or not os.path.isdir(a.dir), script=SCRIPT, path=p)
    elif cmd == "from-prior-art":
        pa_path = os.path.join(a.dir, "prior-art.json")
        if not os.path.exists(pa_path):
            raise UsageError("prior-art.json not found in %s" % a.dir)
        with open(pa_path, encoding="utf-8") as fh:
            try:
                pa = json.load(fh)
            except ValueError as e:
                raise UsageError("%s is not valid JSON: %s" % (pa_path, e))
        check_schema(pa, SCHEMA_PRIOR_ART, pa_path)
        out = under_dir(a.out, a.dir) if a.out else os.path.join(a.dir, "charts", "patentability.json")
        previous = None
        if os.path.exists(out):
            try:
                with open(out, encoding="utf-8") as fh:
                    previous = json.load(fh)
            except ValueError:
                previous = None
            if not a.force and previous and any(c.get("verified") for c in previous.get("cells", []) or []):
                res["text"].append("note: %s exists; verified ticks on unchanged cells are kept" % out)
        label = None
        try:
            with open(os.path.join(a.dir, "state.json"), encoding="utf-8") as fh:
                label = (json.load(fh).get("matter") or {}).get("title")
        except (OSError, ValueError):
            pass
        refs_filter = set(x.strip() for x in a.refs.split(",")) if a.refs else None
        cats = set(x.strip().upper() for x in a.categories.split(",")) if a.categories else None
        chart = build_from_prior_art(pa, refs_filter, cats, label, previous if not a.force else None)
        write_json(out, chart)
        res["written"] = [out]
        res["summary"] = {"refs": len(chart["refs"]), "elements": len(chart["elements"]),
                          "cells": len(chart["cells"]), "needs_evidence": len(chart["needs_evidence"])}
        res["text"].append("wrote %s (%d refs x %d elements)" % (out, len(chart["refs"]), len(chart["elements"])))
        audit(a.dir, "export", no_audit=a.no_audit, script=SCRIPT, path=out)
    else:
        raise UsageError("unknown command %r (render, validate, needs-evidence, from-prior-art)" % cmd)
    return res


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command")

    def common(sp):
        sp.add_argument("--dir", default="patent", help="matter folder (default: patent)")
        sp.add_argument("--json", action="store_true", help="machine-readable output")
        sp.add_argument("--no-audit", action="store_true", help="do not append to audit.jsonl")

    r = sub.add_parser("render", help="render to Markdown / CSV / DOCX")
    r.add_argument("chart")
    r.add_argument("--md", action="store_true")
    r.add_argument("--csv", action="store_true")
    r.add_argument("--docx", action="store_true")
    r.add_argument("--by", choices=["reference", "element"], default="reference",
                   help="Markdown layout: one table per reference (default) or one row per element")
    r.add_argument("--out", help="output base path; relative paths are under --dir (default: next to the chart)")
    common(r)
    v = sub.add_parser("validate", help="check kinds, states, cells")
    v.add_argument("chart")
    common(v)
    n = sub.add_parser("needs-evidence", help="list cells that need more evidence")
    n.add_argument("chart")
    common(n)
    f = sub.add_parser("from-prior-art", help="build a patentability chart from prior-art.json element_map")
    f.add_argument("--out", help="output chart path; relative paths are under --dir "
                                 "(default <dir>/charts/patentability.json)")
    f.add_argument("--refs", help="comma-separated reference ids to include")
    f.add_argument("--categories", help="comma-separated categories to include (X,Y,A,P,E)")
    f.add_argument("--force", action="store_true", help="rebuild without keeping earlier verified ticks")
    common(f)
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)
    if not args.command:
        p.print_help()
        return 2
    try:
        res = run(args)
    except UsageError as e:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "exit_code": 2, "error": str(e), "findings": [], "checks_run": [],
                              "checks_skipped": [], "summary": {}}, indent=2))
        else:
            print("ERROR: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({k: v for k, v in res.items() if k != "text"}, indent=2, ensure_ascii=False))
    else:
        for line in res.get("text", []):
            print(line)
        for f in res.get("findings", []):
            print("%-5s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
        if res.get("checks_run"):
            print("Checks run: %s" % ", ".join(res["checks_run"]))
        s = res.get("summary") or {}
        if "blocking" in s:
            print("Summary: %d BLOCK, %d WARN" % (s["blocking"], s.get("warnings", 0)))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
