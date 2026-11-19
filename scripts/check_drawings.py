#!/usr/bin/env python3
"""check_drawings.py - drawings vs specification, and drawing sheets vs 37 CFR 1.84.

Usage:
  python3 scripts/check_drawings.py --figures draft/figures.json --spec draft/spec.md
         [--manifest draft/out/drawings-manifest.json] [--pdf draft/out/drawings.pdf]
         [--dir patent] [--json] [--no-audit]

Checks (each listed as ran or skipped):
  figures-schema        figures.json parses and is patentassist/figures@1
  numerals-fig-to-spec  every numeral in a figure is mentioned in the description      1.84(p)(5)
  numerals-spec-to-fig  every numeral mentioned in the description appears in a figure  1.84(p)(5)
  numeral-unique        one numeral = one part across all figures                       1.84(p)(4)
  numeral-names         spec element name and figure label for a numeral share a word  (WARN)
  fig-numbering         views numbered FIG. 1, 2, 3 ... consecutively                    1.84(u)(1)
  fig-brief             FIG. ids <-> Brief Description of the Drawings, both ways       37 CFR 1.74
  fig-detailed          every FIG. referred to in the Detailed Description              37 CFR 1.74
  manifest-fresh        drawings were built from the current figures.json
  manifest-numerals     built sheets carry the same numerals as figures.json
  edge-crossings        EDGE_CROSSES_NODE (BLOCK): a connector drawn through a box that is not one of its
                        ends or an enclosing container of an end; EDGE_CROSSES_NUMERAL (WARN): a connector
                        through a reference numeral (manifest geometry)                1.84(p)(3), (q), (r)
  pdf-page-size         every sheet letter or A4, all the same size                     1.84(f)
  pdf-margins           all marks inside the sight (margins T2.5 L2.5 R1.5 B1.0 cm)     1.84(g)
  pdf-text-height       numerals and letters >= 0.32 cm high (cap height)              1.84(p)(3)
  pdf-black-only        no colored or gray lines, fills, or images                      1.84(a)(1), (l)
  pdf-fonts-embedded    every font embedded (Patent Center PDF requirement)
  pdf-sheet-numbers     "n/N" at the top center of each sheet, inside the sight         1.84(t)
  pdf-fig-labels        each "FIG. n" label present on the sheets                       1.84(u)
Exit codes: 0 no blocking findings, 1 blocking findings, 2 usage/input error.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _specparse as sp  # noqa: E402
from _specparse import GENERIC_NAMES  # noqa: E402

PT_PER_CM = 72.0 / 2.54
MIN_TEXT_CM = 0.32
SHEETS_PT = {"letter": (612.0, 792.0), "a4": (595.2756, 841.8898)}
MARGINS_CM = {"top": 2.5, "left": 2.5, "right": 1.5, "bottom": 1.0}  # 1.84(g)
# cap height / em for common fonts; unknown fonts use a conservative 0.66
CAP_RATIOS = [("vera", 0.729), ("dejavu", 0.729), ("helvetica", 0.718), ("arial", 0.716),
              ("liberationsans", 0.716), ("calibri", 0.644), ("times", 0.662), ("liberationserif", 0.662),
              ("courier", 0.571), ("cambria", 0.667), ("georgia", 0.692), ("verdana", 0.727)]


class UsageError(Exception):
    pass


# --------------------------------------------------------------------------- spec parsing
# Section, figure-reference and numeral parsing live in _specparse.py, shared with check_spec.py.

def split_sections(md: str) -> List[Tuple[str, str]]:
    """[(HEADING, body)] for the '##' sections (and a leading '#' H1); '###' stays inside its section."""
    return [(s["heading"].upper(), sp.body_text(s)) for s in sp.parse_spec(md)["sections"]]


def find_section(secs, *needles) -> Optional[str]:
    for h, b in secs:
        if any(n in h for n in needles):
            return b
    return None


def fig_refs(text: str) -> Set[str]:
    """All figure ids cited in text: 'FIG. 1', 'FIGS. 2A-2C', 'FIGS. 3 and 4' -> {'1','2A','2B','2C','3','4'}."""
    return set(i for i, _ in sp.fig_ids_in(text))


def norm_fig_id(fid: str) -> str:
    return sp.norm_fig_id(fid)


def spec_numerals(text: str) -> Dict[str, List[str]]:
    """numeral -> list of element names found in the description (shared parser)."""
    return sp.numeral_names(text)


def word_in(numeral: str, text: str) -> bool:
    return re.search(r"(?<![\w.,/])" + re.escape(numeral) + r"(?![\w]|[.,/]\d)", text) is not None


# --------------------------------------------------------------------------- figures parsing

def figure_numerals(fig: dict) -> List[Tuple[str, str]]:
    """[(numeral, label)] declared in one figure spec."""
    out = []

    def add(obj, default_label=""):
        if isinstance(obj, dict) and obj.get("numeral") not in (None, ""):
            out.append((str(obj["numeral"]).strip(), str(obj.get("label") or default_label)))
    t = (fig.get("type") or "").lower()
    if t == "flowchart":
        for s in fig.get("steps") or []:
            add(s)
    elif t == "block":
        for n in fig.get("nodes") or []:
            add(n)
    elif t == "sequence":
        for p in fig.get("participants") or fig.get("lifelines") or []:
            add(p)
        for m in fig.get("messages") or []:
            add(m)
    elif t == "wireframe":
        dev = fig.get("device")
        if isinstance(dev, dict):
            add(dev, dev.get("kind", "device"))
        for r in fig.get("regions") or []:
            add(r)
    elif t == "graph":
        for s in fig.get("series") or []:
            add(s)
        for b in fig.get("bars") or []:
            add(b)
    elif t == "image":
        for m in fig.get("numerals") or fig.get("callouts") or []:
            add(m)
    else:
        for key in ("nodes", "steps", "regions", "numerals", "participants", "messages", "series"):
            for o in fig.get(key) or []:
                add(o)
    return out


def _norm_label(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).split())


# --------------------------------------------------------------------------- PDF inspection

def cap_ratio(font_name: str) -> float:
    f = re.sub(r"[^a-z]", "", str(font_name).lower())
    for key, r in CAP_RATIOS:
        if key in f:
            return r
    return 0.66


def _is_black(c) -> bool:
    if c is None:
        return True
    return all(v <= 0.02 for v in c)


def _is_white(c) -> bool:
    return c is not None and all(v >= 0.98 for v in c)


def inspect_pdf(path: str, add, ran, skipped, manifest: Optional[dict], fig_ids: List[str], single: bool):
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None
    if fitz is None:
        # fall back to page sizes with pypdf
        try:
            from pypdf import PdfReader
        except ImportError:
            for c in ("pdf-page-size", "pdf-margins", "pdf-text-height", "pdf-black-only", "pdf-fonts-embedded",
                      "pdf-sheet-numbers", "pdf-fig-labels"):
                skipped.append({"check": c, "reason": "neither PyMuPDF (pip install pymupdf) nor pypdf installed"})
            return
        r = PdfReader(path)
        _page_sizes([(float(p.mediabox.width), float(p.mediabox.height)) for p in r.pages], add)
        ran.append("pdf-page-size")
        for c in ("pdf-margins", "pdf-text-height", "pdf-black-only", "pdf-fonts-embedded",
                  "pdf-sheet-numbers", "pdf-fig-labels"):
            skipped.append({"check": c, "reason": "PyMuPDF not installed (pip install pymupdf)"})
        return
    doc = fitz.open(path)
    sizes = [(p.rect.width, p.rect.height) for p in doc]
    sheet = _page_sizes(sizes, add)
    ran.append("pdf-page-size")
    n = len(doc)
    margin_bad = 0
    small = []
    colors = []
    no_num = []
    all_text = []
    for pi, page in enumerate(doc):
        W, H = page.rect.width, page.rect.height
        sx0 = MARGINS_CM["left"] * PT_PER_CM
        sy0 = MARGINS_CM["top"] * PT_PER_CM
        sx1 = W - MARGINS_CM["right"] * PT_PER_CM
        sy1 = H - MARGINS_CM["bottom"] * PT_PER_CM
        tol = 0.5

        def outside(r):
            return r.x0 < sx0 - tol or r.y0 < sy0 - tol or r.x1 > sx1 + tol or r.y1 > sy1 + tol
        for d in page.get_drawings():
            r = d.get("rect")
            if r is not None and outside(r):
                margin_bad += 1
                if margin_bad <= 5:
                    add("BLOCK", "outside-sight", "sheet %d" % (pi + 1),
                        "a line or shape at (%.1f, %.1f)-(%.1f, %.1f) cm runs into the margin (1.84(g))"
                        % (r.x0 / PT_PER_CM, r.y0 / PT_PER_CM, r.x1 / PT_PER_CM, r.y1 / PT_PER_CM))
            for key in ("color", "fill"):
                c = d.get(key)
                if c is not None and not _is_black(c) and not (key == "fill" and _is_white(c)):
                    colors.append((pi + 1, key, tuple(round(v, 2) for v in c)))
        td = page.get_text("dict")
        page_text = []
        for blk in td.get("blocks", []):
            if blk.get("type") == 1:   # image block
                r = fitz.Rect(blk["bbox"])
                if outside(r):
                    margin_bad += 1
                    add("BLOCK", "outside-sight", "sheet %d" % (pi + 1), "an image runs into the margin (1.84(g))")
                continue
            for line in blk.get("lines", []):
                for sp in line.get("spans", []):
                    txt = sp.get("text", "").strip()
                    if not txt:
                        continue
                    page_text.append(txt)
                    r = fitz.Rect(sp["bbox"])
                    size = float(sp.get("size", 0))
                    capr = cap_ratio(sp.get("font", ""))
                    cap_cm = size * capr / PT_PER_CM
                    # a glyph box is ascender-descender; check the cap-height core instead of the box
                    core = fitz.Rect(r.x0, r.y1 - size * 0.24 - size * capr, r.x1, r.y1 - size * 0.24)
                    if outside(core):
                        margin_bad += 1
                        if margin_bad <= 5:
                            add("BLOCK", "outside-sight", "sheet %d" % (pi + 1),
                                "text %r runs into the margin (1.84(g))" % txt[:20])
                    if cap_cm < MIN_TEXT_CM - 1e-3:
                        small.append((pi + 1, txt[:20], round(cap_cm, 3)))
                    c = sp.get("color", 0)
                    if isinstance(c, int) and c != 0:
                        colors.append((pi + 1, "text", "#%06x" % c))
        # images: color or gray content
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 3:
                    colors.append((pi + 1, "image", "color image (RGB/CMYK)"))
                elif pix.n - pix.alpha == 1 and pix.width * pix.height <= 4000000:
                    samples = pix.samples
                    step = max(1, len(samples) // 200000)
                    grays = sum(1 for v in samples[::step] if 24 < v < 232)
                    if grays > 0.02 * (len(samples[::step]) or 1):
                        add("WARN", "gray-image", "sheet %d" % (pi + 1),
                            "image has gray tones; drawings must be black line art (1.84(a)(1), (l)) - "
                            "photographs need 1.84(b) conditions")
            except Exception:
                pass
        all_text.append(page_text)
        want = "%d/%d" % (pi + 1, n)
        top_ok = False
        for blk in td.get("blocks", []):
            for line in blk.get("lines", []):
                for sp in line.get("spans", []):
                    if sp.get("text", "").strip() == want:
                        r = fitz.Rect(sp["bbox"])
                        if abs((r.x0 + r.x1) / 2 - W / 2) < 0.2 * W and r.y1 < sy0 + 0.25 * (sy1 - sy0) and r.y0 >= sy0 - 0.5:
                            top_ok = True
        if not top_ok:
            no_num.append(pi + 1)
    ran += ["pdf-margins", "pdf-text-height", "pdf-black-only"]
    for (pg, txt, cm) in small[:10]:
        add("BLOCK", "text-too-small", "sheet %d" % pg,
            "%r is %.3f cm high; numerals and letters must be at least 0.32 cm (1.84(p)(3))" % (txt, cm))
    if len(small) > 10:
        add("BLOCK", "text-too-small", "drawings", "%d more text items below 0.32 cm" % (len(small) - 10))
    for (pg, key, c) in colors[:10]:
        add("BLOCK", "not-black", "sheet %d" % pg,
            "%s uses %s; drawings must be black on white (1.84(a)(1), (l)); color needs a petition under 1.84(a)(2)"
            % (key, c))
    # fonts embedded
    not_emb = set()
    for pi in range(n):
        for f in doc.get_page_fonts(pi):
            ext, basefont = f[1], f[3]
            if ext in ("n/a", "", None):
                not_emb.add(basefont)
    ran.append("pdf-fonts-embedded")
    for bf in sorted(not_emb):
        add("BLOCK", "font-not-embedded", "drawings", "font %s is not embedded; Patent Center rejects PDFs "
                                                      "with non-embedded fonts" % bf)
    ran.append("pdf-sheet-numbers")
    for pg in no_num:
        add("WARN", "sheet-number", "sheet %d" % pg,
            "no \"%d/%d\" found at the top center of the sight (1.84(t))" % (pg, n))
    ran.append("pdf-fig-labels")
    joined = " ".join(" ".join(t) for t in all_text)
    if single:
        if re.search(r"\bFIG\.", joined):
            add("WARN", "single-view-label", "drawings",
                "only one view: it must not be numbered and \"FIG.\" must not appear (1.84(u)(1))")
    else:
        for fid in fig_ids:
            lab = "FIG. " + norm_fig_id(fid)
            if not re.search(re.escape(lab) + r"(?![0-9A-Z])", joined):
                add("WARN", "fig-label-missing", fid, "label %r not found on any sheet (1.84(u))" % lab)
    doc.close()


def _page_sizes(sizes, add):
    if not sizes:
        add("BLOCK", "empty-pdf", "drawings", "PDF has no pages")
        return None
    names = []
    for i, (w, h) in enumerate(sizes):
        nm = None
        for k, (sw, sh) in SHEETS_PT.items():
            if abs(w - sw) < 2.0 and abs(h - sh) < 2.0:
                nm = k
        if nm is None:
            add("BLOCK", "page-size", "sheet %d" % (i + 1),
                "%.1f x %.1f cm is neither A4 (21.0 x 29.7) nor letter (21.6 x 27.9) portrait (1.84(f))"
                % (w / PT_PER_CM, h / PT_PER_CM))
        names.append(nm)
    if len(set(names)) > 1:
        add("BLOCK", "page-size-mixed", "drawings", "all drawing sheets must be the same size (1.84(f))")
    return names[0]


# --------------------------------------------------------------------------- main check

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check(figures_path: str, spec_path: str, manifest_path: Optional[str] = None,
          pdf_path: Optional[str] = None) -> dict:
    findings = []
    ran = []
    skipped = []

    def add(level, code, where, msg):
        findings.append({"level": level, "code": code, "where": where, "message": msg})

    # ---- inputs
    try:
        with open(figures_path, "r", encoding="utf-8") as fh:
            figs = json.load(fh)
    except (OSError, ValueError) as ex:
        raise UsageError("cannot read figures file %s: %s" % (figures_path, ex))
    schema = str(figs.get("schema", ""))
    if not schema.startswith("patentassist/figures@") or schema.split("@")[-1].split(".")[0] != "1":
        raise UsageError("unsupported figures schema %r (want patentassist/figures@1)" % schema)
    ran.append("figures-schema")
    try:
        with open(spec_path, "r", encoding="utf-8") as fh:
            spec = fh.read()
    except OSError as ex:
        raise UsageError("cannot read spec %s: %s" % (spec_path, ex))
    parsed = sp.parse_spec(spec)
    desc = sp.description_text(parsed)
    fig_list = figs.get("figures") or []
    fig_ids = [f.get("id", "?") for f in fig_list]
    single = len(fig_list) == 1

    # ---- numerals in figures
    fig_nums = {}  # numeral -> [(fig id, label)]
    label_nums = {}
    for f in fig_list:
        for (n, lab) in figure_numerals(f):
            fig_nums.setdefault(n, []).append((f.get("id", "?"), lab))
            label_nums.setdefault(_norm_label(lab), set()).add(n)
    ran.append("numeral-unique")
    for n, uses in sorted(fig_nums.items()):
        labs = {}
        for fid, lab in uses:
            labs.setdefault(_norm_label(lab), []).append(fid)
        if len(labs) > 1:
            desc_ = "; ".join("%r in %s" % (k, ", ".join(sorted(set(v)))) for k, v in labs.items())
            add("BLOCK", "numeral-reused", "numeral %s" % n,
                "one numeral names different parts: %s (1.84(p)(4))" % desc_)
    for lab, ns in sorted(label_nums.items()):
        if lab and len(ns) > 1:
            add("WARN", "label-two-numerals", lab,
                "the same label carries numerals %s; the same part must keep one numeral (1.84(p)(4))"
                % ", ".join(sorted(ns)))

    # ---- numerals both ways
    ran.append("numerals-fig-to-spec")
    for n in sorted(fig_nums, key=lambda z: (len(z), z)):
        if not word_in(n, desc):
            add("BLOCK", "numeral-not-in-spec", ", ".join(sorted(set(f for f, _ in fig_nums[n]))),
                "numeral %s (%s) appears in the drawings but not in the description (1.84(p)(5))"
                % (n, fig_nums[n][0][1]))
    found = spec_numerals(desc)
    ran.append("numerals-spec-to-fig")
    for n in sorted(found, key=lambda z: (len(z), z)):
        if n not in fig_nums:
            names = ", ".join(sorted(set(x for x in found[n] if x))) or "?"
            add("BLOCK", "numeral-not-in-drawings", "spec",
                "numeral %s (%s) is in the description but in no figure (1.84(p)(5))" % (n, names))
    ran.append("numeral-names")
    fig_type = {}
    for f in fig_list:
        for (n, _) in figure_numerals(f):
            fig_type.setdefault(n, (f.get("type") or "").lower())

    def same_word(a, b):
        return a == b or (len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a) or a[:5] == b[:5]))
    for n, names in found.items():
        if n not in fig_nums or not names or fig_type.get(n) == "flowchart":
            continue
        fl = set(_norm_label(fig_nums[n][0][1]).split())
        words = set()
        for nm in names:
            words.update(_norm_label(nm).split())
        if words & GENERIC_NAMES:
            continue
        if fl and not any(same_word(a, b) for a in fl for b in words):
            add("WARN", "numeral-name-mismatch", "numeral %s" % n,
                "figure calls it %r, the description calls it %r" % (fig_nums[n][0][1], sorted(set(names))[0]))

    # ---- FIG numbering and references
    ran.append("fig-numbering")
    ids = [norm_fig_id(x) for x in fig_ids]
    if not single:
        nums = []
        for i in ids:
            m = re.match(r"^(\d+)([A-Z]?)$", i)
            if not m:
                add("BLOCK", "fig-id", i, "figure id must look like \"FIG. 3\" or \"FIG. 3A\" (1.84(u)(1))")
                continue
            nums.append(int(m.group(1)))
        uniq = sorted(set(nums))
        if uniq and uniq != list(range(1, uniq[-1] + 1)):
            add("BLOCK", "fig-numbering", "figures",
                "views must be numbered consecutively from FIG. 1 (found %s) (1.84(u)(1))" % uniq)
        if nums != sorted(nums):
            add("WARN", "fig-order", "figures", "figures are not listed in numeric order")
    bsec, dsec = sp.section(parsed, "BRIEF_DRAWINGS"), sp.section(parsed, "DETAILED_DESCRIPTION")
    brief = sp.body_text(bsec) if bsec else None
    detailed = sp.body_text(dsec) if dsec else None
    if brief is None:
        skipped.append({"check": "fig-brief", "reason": "spec has no BRIEF DESCRIPTION OF THE DRAWINGS heading"})
        add("BLOCK", "no-brief-description", "spec",
            "drawings exist but the spec has no Brief Description of the Drawings (37 CFR 1.74)")
    else:
        ran.append("fig-brief")
        if single:
            if not brief.strip():
                add("BLOCK", "brief-empty", "spec", "Brief Description of the Drawings is empty (37 CFR 1.74)")
        else:
            bref = fig_refs(brief)
            for i, raw in zip(ids, fig_ids):
                if i not in bref:
                    add("BLOCK", "fig-not-in-brief", raw,
                        "%s has no line in the Brief Description of the Drawings (37 CFR 1.74)" % raw)
            for r in sorted(bref - set(ids)):
                add("BLOCK", "brief-fig-missing", "FIG. %s" % r,
                    "Brief Description describes FIG. %s but figures.json has no such figure" % r)
    if detailed is None:
        skipped.append({"check": "fig-detailed", "reason": "spec has no DETAILED DESCRIPTION heading"})
    else:
        ran.append("fig-detailed")
        if not single:
            dref = fig_refs(detailed)
            for i, raw in zip(ids, fig_ids):
                if i not in dref:
                    add("BLOCK", "fig-not-in-detailed", raw,
                        "the Detailed Description never refers to %s (37 CFR 1.74)" % raw)
            for r in sorted(dref - set(ids)):
                add("BLOCK", "detailed-fig-missing", "FIG. %s" % r,
                    "Detailed Description cites FIG. %s but figures.json has no such figure" % r)

    # ---- manifest
    manifest = None
    if manifest_path is None:
        cand = os.path.join(os.path.dirname(os.path.abspath(figures_path)), "out", "drawings-manifest.json")
        manifest_path = cand if os.path.exists(cand) else None
    if manifest_path and os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        ran.append("manifest-fresh")
        if manifest.get("figures_sha256") != _sha256(figures_path):
            add("BLOCK", "drawings-stale", "drawings",
                "drawings were built from an older figures.json; rebuild with drawings.py build")
        ran.append("manifest-numerals")
        built = {}
        for mf in manifest.get("figures", []):
            built[norm_fig_id(mf["id"])] = set(n["numeral"] for n in mf.get("numerals", []))
        for f in fig_list:
            want = set(n for n, _ in figure_numerals(f))
            have = built.get(norm_fig_id(f.get("id", "")))
            if have is None:
                add("BLOCK", "figure-not-built", f.get("id", "?"), "figure is missing from the built drawings")
            elif want != have:
                add("BLOCK", "built-numerals-differ", f.get("id", "?"),
                    "built sheet numerals differ from figures.json (missing %s, extra %s)"
                    % (sorted(want - have), sorted(have - want)))
        for mf in manifest.get("figures", []):
            if mf.get("min_cap_height_cm", 1) < MIN_TEXT_CM - 1e-4:
                add("BLOCK", "text-too-small", mf["id"],
                    "smallest text is %.3f cm high (1.84(p)(3) needs 0.32 cm)" % mf["min_cap_height_cm"])
        for fd in manifest.get("findings", []):
            if fd.get("code") in ("figure-too-large", "lead-lines-cross"):
                findings.append(fd)
        geo = [mf for mf in manifest.get("figures", []) if "edges" in mf]
        if geo:
            import drawings as _dw
            ran.append("edge-crossings")
            for mf in geo:
                nodes = [dict(nd, box=nd["box_pt"]) for nd in mf.get("nodes", [])]
                edges = [dict(ed, pts=ed["pts_pt"]) for ed in mf.get("edges", [])]
                nums = [dict(nm, text_bbox=nm["text_bbox_pt"]) for nm in mf.get("numerals", []) if nm.get("text_bbox_pt")]
                for lvl, code, msg in _dw.edge_crossings(nodes, edges, nums):
                    add(lvl, code, mf["id"], msg)
        else:
            skipped.append({"check": "edge-crossings",
                            "reason": "manifest has no edge geometry (rebuild with drawings.py build)"})
        if pdf_path is None and manifest.get("pdf"):
            pdf_path = os.path.join(os.path.dirname(os.path.abspath(manifest_path)), manifest["pdf"])
    else:
        for c in ("manifest-fresh", "manifest-numerals", "edge-crossings"):
            skipped.append({"check": c, "reason": "no drawings-manifest.json (run drawings.py build or pass --manifest)"})

    # ---- PDF
    if pdf_path and os.path.exists(pdf_path):
        inspect_pdf(pdf_path, add, ran, skipped, manifest, fig_ids, single)
    else:
        for c in ("pdf-page-size", "pdf-margins", "pdf-text-height", "pdf-black-only", "pdf-fonts-embedded",
                  "pdf-sheet-numbers", "pdf-fig-labels"):
            skipped.append({"check": c, "reason": "no drawings PDF (pass --pdf or build drawings first)"})

    blocking = sum(1 for f in findings if f["level"] == "BLOCK")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    return {"findings": findings, "checks_run": ran, "checks_skipped": skipped,
            "summary": {"blocking": blocking, "warnings": warns, "figures": len(fig_list),
                        "numerals_in_figures": len(fig_nums), "numerals_in_spec": len(found),
                        "complete": not skipped}}


def _resolve(path: Optional[str], d: str) -> Optional[str]:
    if path is None:
        return None
    if os.path.isabs(path) or os.path.exists(path):
        return path
    alt = os.path.join(d, path)
    return alt if os.path.exists(alt) else path


def _audit(d, rec, no_audit):
    if no_audit or not d or not os.path.isdir(d):
        return
    rec = dict(rec)
    rec["ts"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with open(os.path.join(d, "audit.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def run(args: dict) -> dict:
    """Tool entry point. args: {figures, spec, manifest?, pdf?, dir?, no_audit?}"""
    d = args.get("dir", "patent")
    res = check(_resolve(args["figures"], d), _resolve(args["spec"], d),
                _resolve(args.get("manifest"), d), _resolve(args.get("pdf"), d))
    _audit(d, {"kind": "check", "script": "check_drawings.py", "blocking": res["summary"]["blocking"],
               "warnings": res["summary"]["warnings"]}, bool(args.get("no_audit")))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check drawings against the spec and 37 CFR 1.84")
    ap.add_argument("--figures", default="draft/figures.json")
    ap.add_argument("--spec", default="draft/spec.md")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--pdf", default=None)
    ap.add_argument("--dir", default="patent")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-audit", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = run({"figures": a.figures, "spec": a.spec, "manifest": a.manifest, "pdf": a.pdf,
                   "dir": a.dir, "no_audit": a.no_audit})
    except UsageError as ex:
        print(json.dumps({"error": str(ex)}) if a.json else "error: %s" % ex, file=sys.stdout if a.json else sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print("%s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
        print("ran: %s" % ", ".join(res["checks_run"]))
        for s in res["checks_skipped"]:
            print("skipped: %s (%s)" % (s["check"], s["reason"]))
        s = res["summary"]
        verdict = "no blocking issues" if s["blocking"] == 0 and s["complete"] else (
            "no blocking issues in the checks that ran (some skipped)" if s["blocking"] == 0 else
            "%d blocking issue(s)" % s["blocking"])
        print("%s; %d warning(s)" % (verdict, s["warnings"]))
    return 1 if res["summary"]["blocking"] else 0


if __name__ == "__main__":
    sys.exit(main())
