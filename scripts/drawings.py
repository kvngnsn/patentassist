#!/usr/bin/env python3
"""drawings.py - figures.json -> one SVG per figure + 37 CFR 1.84 drawing sheets (PDF).

Usage:
  python3 scripts/drawings.py build draft/figures.json --out draft/out/ [--dir patent] [--json] [--no-audit]

Figure types (patentassist/figures@1): flowchart, block, sequence, wireframe, graph, image.
Outputs in --out: FIG-<n>.svg per figure, drawings.pdf (all sheets, vector, embedded font),
drawings-manifest.json (figure -> sheet, numerals, bounding boxes, text sizes) for check_drawings.py.

Rules encoded (37 CFR 1.84, text checked 2026-11-18 against eCFR):
  1.84(a)(1) black lines only; no color.        1.84(f) letter 21.6x27.9 cm or A4 21.0x29.7 cm.
  1.84(g) margins top 2.5, left 2.5, right 1.5, bottom 1.0 cm; no frame around the sight.
  1.84(i) views never placed inside another view; all upright.
  1.84(l) lines solid black, uniformly thick.   1.84(m) no solid black areas except bar graphs.
  1.84(p)(1) numerals never encircled or bracketed.  1.84(p)(3) numerals and letters >= 0.32 cm high.
  1.84(p)(4) one numeral = one part across all views.
  1.84(q) lead lines short, start next to the numeral, end at the feature, should not cross.
  1.84(r)(3) arrows show direction of flow.
  1.84(t) sheet number "n/N" centered at the top INSIDE the sight (not in the margin), larger than numerals.
  1.84(u)(1) views numbered "FIG. 1"... in order; a single view gets no "FIG." label.
  1.84(u)(2) view numbers larger than numerals.
Patent Center rejects PDFs with non-embedded fonts, so text uses the TrueType Bitstream Vera Sans
that ships inside reportlab (embedded as a subset). Its cap height is 0.729 em (measured), so
0.32 cm (9.07 pt) needs a font size of at least 12.44 pt; we never go below TEXT_MIN = 12.5 pt.
Labels are upper-cased by default so every letter (not just capitals) meets the 0.32 cm rule.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple

SCHEMA_FIGURES = "patentassist/figures@1"
SCHEMA_MANIFEST = "patentassist/drawings-manifest@1"

PT_PER_CM = 72.0 / 2.54
SHEETS = {  # 1.84(f)
    "letter": (612.0, 792.0),          # 21.6 x 27.9 cm
    "a4": (595.2756, 841.8898),        # 21.0 x 29.7 cm
}
MARGINS_CM = {"top": 2.5, "left": 2.5, "right": 1.5, "bottom": 1.0}  # 1.84(g)
SAFETY_PT = 0.2 * PT_PER_CM            # extra inset so nothing touches the sight edge

CAP_RATIO = 0.729                      # Vera cap height / em (measured by rendering "H")
DIGIT_RATIO = 0.758                    # tallest digit incl. overshoot
MIN_TEXT_CM = 0.32                     # 1.84(p)(3)
TEXT_MIN = 12.5                        # pt; 12.5 * 0.729 = 9.11 pt = 0.321 cm
TEXT_PREF = 13.5
TEXT_EDGE = 13.0                       # edge / branch labels (room to scale 0.96)
NUM_SIZE = 14.0                        # reference numerals
FIG_SIZE = 20.0                        # "FIG. n" - larger than numerals, 1.84(u)(2)
SHEETNO_SIZE = 16.0                    # sheet number - larger than numerals, 1.84(t)
LW = 1.1                               # line weight for outlines and connectors (pt)
LW_LEAD = 0.75                         # lead lines
AH_LEN = 8.0                           # arrowhead length
AH_HALF = 3.4                          # arrowhead half width
LINE_H = 1.22                          # line height multiplier

FONT = "PAVera"
FONT_B = "PAVeraBd"
_FONT_FILES = {FONT: "Vera.ttf", FONT_B: "VeraBd.ttf"}
_rl_ready = None  # type: Optional[bool]


class UsageError(Exception):
    pass


# --------------------------------------------------------------------------- fonts / metrics

def _reportlab():
    """Register the embedded fonts. Returns True when reportlab is usable."""
    global _rl_ready
    if _rl_ready is not None:
        return _rl_ready
    try:
        import reportlab
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        d = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        for name, fn in _FONT_FILES.items():
            pdfmetrics.registerFont(TTFont(name, os.path.join(d, fn)))
        _rl_ready = True
    except Exception:
        _rl_ready = False
    return _rl_ready


def text_width(s: str, size: float, bold: bool = False) -> float:
    if _reportlab():
        from reportlab.pdfbase import pdfmetrics
        return pdfmetrics.stringWidth(s, FONT_B if bold else FONT, size)
    # fallback approximation (Vera-like proportions)
    w = 0.0
    for ch in s:
        if ch.isupper():
            w += 0.70
        elif ch.isdigit():
            w += 0.636
        elif ch == " ":
            w += 0.318
        else:
            w += 0.56
    return w * size * (1.07 if bold else 1.0)


def wrap(text: str, size: float, max_w: float, bold: bool = False) -> List[str]:
    lines = []  # type: List[str]
    for para in str(text).split("\n"):
        words = para.split()
        cur = ""
        for word in words:
            cand = (cur + " " + word).strip()
            if text_width(cand, size, bold) <= max_w or not cur:
                if not cur and text_width(word, size, bold) > max_w:
                    # break an over-long word
                    piece = ""
                    for ch in word:
                        if text_width(piece + ch, size, bold) > max_w and piece:
                            lines.append(piece)
                            piece = ch
                        else:
                            piece += ch
                    cur = piece
                else:
                    cur = cand
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines or [""]


def fit_text(text: str, max_w: float, pref: float = TEXT_PREF, mn: float = TEXT_MIN,
             max_lines: int = 3, bold: bool = False) -> Tuple[float, List[str]]:
    """Shrink from pref toward mn (never below) until the text fits in max_lines lines.
    If it still does not fit, return mn and however many lines are needed (box grows)."""
    words = str(text).split()

    def eff(sz):   # never split a word: widen to the longest word instead (the box grows)
        return max([max_w] + [text_width(w_, sz, bold) for w_ in words])
    size = pref
    while size >= mn - 1e-6:
        lines = wrap(text, size, eff(size), bold)
        if len(lines) <= max_lines and eff(size) <= max_w + 1e-6:
            return size, lines
        size -= 0.5
    size = pref
    while size >= mn - 1e-6:
        lines = wrap(text, size, eff(size), bold)
        if len(lines) <= max_lines:
            return size, lines
        size -= 0.5
    return mn, wrap(text, mn, eff(mn), bold)


def block_w(lines: List[str], size: float, bold: bool = False) -> float:
    return max([text_width(l, size, bold) for l in lines] + [0.0])


# --------------------------------------------------------------------------- display list

class Fig:
    """Figure-local display list. Coordinates in points, origin top-left, y down."""

    def __init__(self, fid: str):
        self.id = fid
        self.items = []      # type: List[dict]
        self.numerals = []   # type: List[dict]
        self.warnings = []   # type: List[str]
        self.leads = []      # type: List[Tuple[Tuple[float, float], Tuple[float, float]]]
        # geometry for the manifest and the crossing checks (figure coordinates):
        self.nodes = []      # type: List[dict]  {id, label, numeral, parent, container, box:[x0,y0,x1,y1]}
        self.edges = []      # type: List[dict]  {from, to, pts:[(x, y), ...], label}
        self.edge_labels = []  # type: List[dict]  {edge, text, box}

    # primitives -------------------------------------------------------------
    def line(self, pts, lw=LW, dash=None, arrow_end=False, arrow_start=False):
        pts = [tuple(map(float, p)) for p in pts]
        if arrow_end and len(pts) >= 2:
            pts[-1] = self._arrow(pts[-2], pts[-1])
        if arrow_start and len(pts) >= 2:
            pts[0] = self._arrow(pts[1], pts[0])
        self.items.append({"t": "line", "pts": pts, "lw": lw, "dash": dash})

    def _arrow(self, a, b):
        """Add a filled arrowhead with its tip at b; return the shortened line end."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        bx, by = b[0] - ux * AH_LEN, b[1] - uy * AH_LEN
        px, py = -uy * AH_HALF, ux * AH_HALF
        self.items.append({"t": "poly", "pts": [b, (bx + px, by + py), (bx - px, by - py)],
                           "lw": 0.5, "fill": True, "closed": True})
        return (b[0] - ux * AH_LEN * 0.7, b[1] - uy * AH_LEN * 0.7)

    def rect(self, x, y, w, h, r=0.0, lw=LW, dash=None):
        self.items.append({"t": "rect", "x": x, "y": y, "w": w, "h": h, "r": r, "lw": lw, "dash": dash})

    def poly(self, pts, lw=LW, fill=False, closed=True, dash=None):
        self.items.append({"t": "poly", "pts": [tuple(p) for p in pts], "lw": lw, "fill": fill,
                           "closed": closed, "dash": dash})

    def circle(self, cx, cy, r, lw=LW):
        self.items.append({"t": "circle", "cx": cx, "cy": cy, "r": r, "lw": lw})

    def curve(self, p0, c1, c2, p1, lw=LW_LEAD):
        self.items.append({"t": "curve", "pts": [tuple(p0), tuple(c1), tuple(c2), tuple(p1)], "lw": lw})

    def text(self, x, y, s, size, anchor="start", bold=False, rot=0, kind="label"):
        self.items.append({"t": "text", "x": x, "y": y, "s": str(s), "size": size, "anchor": anchor,
                           "bold": bold, "rot": rot, "kind": kind})

    def image(self, path, x, y, w, h):
        self.items.append({"t": "image", "path": path, "x": x, "y": y, "w": w, "h": h})

    def text_lines(self, cx, cy, lines, size, bold=False, kind="label"):
        """Center a block of lines on (cx, cy)."""
        lh = size * LINE_H
        n = len(lines)
        top = cy - (n * lh) / 2.0
        for i, ln in enumerate(lines):
            # baseline so the cap height is centered inside each line slot
            base = top + i * lh + lh / 2.0 + size * CAP_RATIO / 2.0
            self.text(cx, base, ln, size, anchor="middle", bold=bold, kind=kind)

    # numerals ---------------------------------------------------------------
    def numeral(self, num, label, target, text_pos, anchor="start", size=NUM_SIZE, lead=True):
        """Place reference numeral `num` with a lead line from `target` (on the feature)
        to just beside the numeral text at `text_pos` (baseline point). 1.84(q)."""
        s = str(num)
        w = text_width(s, size)
        tx, ty = text_pos
        if anchor == "start":
            x0 = tx
        elif anchor == "end":
            x0 = tx - w
        else:
            x0 = tx - w / 2.0
        cap = size * DIGIT_RATIO
        bbox = [x0, ty - cap, x0 + w, ty]
        if lead:
            midy = ty - cap / 2.0
            if anchor == "start":
                end = (x0 - 2.5, midy)
            elif anchor == "end":
                end = (x0 + w + 2.5, midy)
            else:
                end = (x0 + w / 2.0, ty - cap - 2.5 if target[1] < ty - cap else ty + 3.0)
            p0 = tuple(target)
            # gentle curve: leave the feature at its own angle, arrive horizontally
            c1 = (p0[0] + (end[0] - p0[0]) * 0.45, p0[1] + (end[1] - p0[1]) * 0.75)
            c2 = (p0[0] + (end[0] - p0[0]) * 0.75, end[1])
            self.curve(p0, c1, c2, end)
            self.leads.append((p0, end))
        self.text(tx, ty, s, size, anchor=anchor, kind="numeral")
        self.numerals.append({"numeral": s, "label": label, "text_bbox": bbox,
                              "target": [round(target[0], 2), round(target[1], 2)]})

    # geometry ---------------------------------------------------------------
    def bbox(self) -> List[float]:
        xs, ys = [], []
        for it in self.items:
            t = it["t"]
            if t in ("line", "poly", "curve"):
                pad = it.get("lw", LW) / 2.0
                for (x, y) in it["pts"]:
                    xs += [x - pad, x + pad]
                    ys += [y - pad, y + pad]
            elif t in ("rect", "image"):
                pad = it.get("lw", 0) / 2.0
                xs += [it["x"] - pad, it["x"] + it["w"] + pad]
                ys += [it["y"] - pad, it["y"] + it["h"] + pad]
            elif t == "circle":
                xs += [it["cx"] - it["r"], it["cx"] + it["r"]]
                ys += [it["cy"] - it["r"], it["cy"] + it["r"]]
            elif t == "text":
                b = text_bbox(it)
                xs += [b[0], b[2]]
                ys += [b[1], b[3]]
        if not xs:
            return [0.0, 0.0, 0.0, 0.0]
        return [min(xs), min(ys), max(xs), max(ys)]

    def shift(self, dx, dy):
        for it in self.items:
            t = it["t"]
            if t in ("line", "poly", "curve"):
                it["pts"] = [(x + dx, y + dy) for (x, y) in it["pts"]]
            elif t in ("rect", "image", "text"):
                it["x"] += dx
                it["y"] += dy
            elif t == "circle":
                it["cx"] += dx
                it["cy"] += dy
        for n in self.numerals:
            b = n["text_bbox"]
            n["text_bbox"] = [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy]
            n["target"] = [n["target"][0] + dx, n["target"][1] + dy]
        self.leads = [((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)) for a, b in self.leads]
        for nd in self.nodes:
            b = nd["box"]
            nd["box"] = [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy]
        for ed in self.edges:
            ed["pts"] = [(x + dx, y + dy) for (x, y) in ed["pts"]]
        for el in self.edge_labels:
            b = el["box"]
            el["box"] = [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy]

    def min_text(self) -> float:
        sizes = [it["size"] for it in self.items if it["t"] == "text"]
        return min(sizes) if sizes else 0.0


def text_bbox(it) -> List[float]:
    s, size = it["s"], it["size"]
    w = text_width(s, size, it.get("bold", False))
    asc, desc = size * 0.76, size * 0.24
    x, y = it["x"], it["y"]
    if it.get("rot"):
        # rotated 90 deg counter-clockwise around (x, y); text runs upward
        if it["anchor"] == "middle":
            y0, y1 = y - w / 2.0, y + w / 2.0
        elif it["anchor"] == "end":
            y0, y1 = y, y + w
        else:
            y0, y1 = y - w, y
        return [x - asc, y0, x + desc, y1]
    if it["anchor"] == "middle":
        x0 = x - w / 2.0
    elif it["anchor"] == "end":
        x0 = x - w
    else:
        x0 = x
    return [x0, y - asc, x0 + w, y + desc]


def _segments_cross(a, b, c, d) -> bool:
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


def seg_hits_rect(a, b, r, shrink=0.0) -> bool:
    """True when segment a-b passes through the interior of rect r = (x0, y0, x1, y1), shrunk by `shrink`
    on every side (Liang-Barsky clipping; touching the border does not count)."""
    x0, y0, x1, y1 = r[0] + shrink, r[1] + shrink, r[2] - shrink, r[3] - shrink
    if x1 <= x0 or y1 <= y0:
        return False
    dx, dy = b[0] - a[0], b[1] - a[1]
    u1, u2 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-12:
            if q <= 1e-9:
                return False
            continue
        t = q / p
        if p < 0:
            u1 = max(u1, t)
        else:
            u2 = min(u2, t)
        if u1 >= u2 - 1e-9:
            return False
    return u2 - u1 > 1e-6


def node_ancestors(nodes: List[dict], nid) -> set:
    """Ids of nid and every container that encloses it."""
    by = {n["id"]: n for n in nodes}
    out = set()
    cur = nid
    while cur is not None and cur in by and cur not in out:
        out.add(cur)
        cur = by[cur].get("parent")
    return out


def edge_crossings(nodes: List[dict], edges: List[dict], numerals: List[dict]):
    """[(level, code, message)] for connectors drawn through a box that is not one of their ends (or an
    enclosing container of an end), and through a reference numeral. Shared by drawings.py (build) and
    check_drawings.py (manifest) so both apply the same rule."""
    out = []
    for ei, e in enumerate(edges):
        ok = node_ancestors(nodes, e.get("from")) | node_ancestors(nodes, e.get("to"))
        pts = [tuple(p) for p in e.get("pts") or []]
        segs = list(zip(pts, pts[1:]))
        name = "%s -> %s" % (e.get("from"), e.get("to"))
        for nd in nodes:
            if nd["id"] in ok:
                continue
            if any(seg_hits_rect(a, b, nd["box"], shrink=0.75) for a, b in segs):
                out.append(("BLOCK", "EDGE_CROSSES_NODE",
                            "connector %s is drawn through box %s (%s); a line through an unrelated part "
                            "misdescribes the connection (1.84(q), (r))" % (name, nd.get("numeral") or nd["id"],
                                                                         nd.get("label", ""))))
        for nm in numerals or []:
            bb = nm.get("text_bbox")
            if bb and any(seg_hits_rect(a, b, bb, shrink=0.3) for a, b in segs):
                out.append(("WARN", "EDGE_CROSSES_NUMERAL",
                            "connector %s runs through reference numeral %s; numerals must stay legible and "
                            "off other lines (1.84(p)(3))" % (name, nm.get("numeral"))))
    return out


def check_lead_crossings(fig: Fig):
    L = fig.leads
    for i in range(len(L)):
        for j in range(i + 1, len(L)):
            if _segments_cross(L[i][0], L[i][1], L[j][0], L[j][1]):
                fig.warnings.append("lead lines cross near %s" % (str([round(v) for v in L[i][0]])))


# --------------------------------------------------------------------------- helpers

def safe_name(fid) -> str:
    """'FIG. 2A' -> 'FIG-2A' (file names for SVG and line-art outputs)."""
    import re as _re
    return _re.sub(r"[^A-Za-z0-9]+", "-", str(fid)).strip("-") or "figure"


def apply_case(s, case):
    """Upper-case labels so every letter meets 0.32 cm, but leave text in parentheses alone:
    it usually holds units, where case carries meaning (mA vs MA, kHz, lux)."""
    s = "" if s is None else str(s)
    if case != "upper":
        return s
    import re as _re
    parts = _re.split(r"(\([^)]*\))", s)
    return "".join(p if p.startswith("(") else p.upper() for p in parts)


def num_str(n) -> str:
    return "" if n is None else str(n).strip()


# --------------------------------------------------------------------------- flowchart

FC_MIN_IN, FC_MAX_IN = 150.0, 250.0
FC_PADX, FC_PADY = 10.0, 9.0
FC_GAP = 36.0
FC_NUM_DX = 20.0


def layout_flowchart(f: dict, case: str) -> Fig:
    fig = Fig(f["id"])
    compact = bool(f.get("_compact"))
    gap0 = 26.0 if compact else FC_GAP
    pady = 6.0 if compact else FC_PADY
    steps = f.get("steps") or []
    if not steps:
        raise UsageError("%s: flowchart has no steps" % f["id"])
    n = len(steps)
    by_num = {}
    for i, s in enumerate(steps):
        k = num_str(s.get("numeral"))
        if k:
            by_num[k] = i

    def kind_of(i):
        k = (steps[i].get("kind") or "step").lower()
        if k in ("terminal", "terminator"):
            return "start" if i == 0 else "end"
        if k in ("process", "io", "action"):
            return "step"
        if k in ("connector", "off-page", "offpage", "off_page"):
            return "connector"
        return k

    kinds = [kind_of(i) for i in range(n)]
    by_label = {}   # off-page connector letter -> step index ("next": "A" jumps to connector A)
    for i in range(n):
        if kinds[i] == "connector":
            by_label[str(steps[i].get("label", "")).strip().upper()] = i
    labels = [apply_case(s.get("label", ""), case) for s in steps]

    # --- sizes
    natural = [text_width(labels[i], TEXT_PREF) for i in range(n) if kinds[i] not in ("decision", "connector")]
    w_in = min(max(natural + [FC_MIN_IN]), FC_MAX_IN)
    boxes = []
    for i in range(n):
        if kinds[i] == "connector":
            # off-page connector: the letter in a circle; the same letter on the next view continues the flow
            size = TEXT_PREF
            d = max(text_width(labels[i], size) + 14.0, 30.0)
            boxes.append({"w": d, "h": d, "size": size, "lines": [labels[i]]})
        elif kinds[i] == "decision":
            dw = min(w_in * 0.78, 200.0)
            size, lines = fit_text(labels[i], dw, max_lines=3)
            tw = block_w(lines, size) + 8.0
            th = len(lines) * size * LINE_H + 4.0
            a = (tw / 2.0) / 0.6
            b = max((th / 2.0) / 0.4, 30.0)
            boxes.append({"w": 2 * a, "h": 2 * b, "size": size, "lines": lines})
        else:
            size, lines = fit_text(labels[i], w_in, max_lines=3)
            h = max(len(lines) * size * LINE_H + 2 * pady, 34.0 if compact else 38.0)
            boxes.append({"w": w_in + 2 * FC_PADX, "h": h, "size": size, "lines": lines})

    # --- edges
    def resolve(t, i):
        if t is None:
            return None
        if isinstance(t, str) and t.lower() == "next":
            return i + 1 if i + 1 < n else None
        k = num_str(t)
        if k not in by_num:
            if k.upper() in by_label:
                return by_label[k.upper()]
            raise UsageError("%s: step %s points to unknown step %s" % (f["id"], num_str(steps[i].get("numeral")), k))
        return by_num[k]

    edges = []  # (src, dst, label)
    for i, s in enumerate(steps):
        if kinds[i] == "decision":
            for key, dflt in (("yes", "YES"), ("no", "NO")):
                if key in s and s[key] is not None:
                    edges.append((i, resolve(s[key], i), apply_case(s.get(key + "_label", dflt), case)))
        elif kinds[i] == "end":
            if s.get("next") is not None:
                edges.append((i, resolve(s["next"], i), apply_case(s.get("next_label", ""), case)))
        else:
            t = s.get("next", "next")
            d = resolve(t, i)
            if d is not None:
                edges.append((i, d, apply_case(s.get("next_label", ""), case)))
    seq_from = {}
    for idx, (a, b, lab) in enumerate(edges):
        if b == a + 1 and a not in seq_from:
            seq_from[a] = idx
    side = [idx for idx in range(len(edges)) if seq_from.get(edges[idx][0]) != idx]
    targets_with_merge = set(edges[idx][1] for idx in side)

    # --- vertical positions
    y = 30.0 if 0 in targets_with_merge else 0.0
    cx = 0.0
    for i in range(n):
        boxes[i]["y"] = y
        boxes[i]["x"] = cx - boxes[i]["w"] / 2.0
        gap = gap0
        if kinds[i] == "decision":
            gap += 8.0
        if (i + 1) in targets_with_merge:
            gap += 6.0
        y += boxes[i]["h"] + gap

    # --- draw shapes
    for i in range(n):
        b = boxes[i]
        x, y0, w, h = b["x"], b["y"], b["w"], b["h"]
        if kinds[i] == "decision":
            fig.poly([(cx, y0), (cx + w / 2, y0 + h / 2), (cx, y0 + h), (cx - w / 2, y0 + h / 2)])
        elif kinds[i] == "connector":
            fig.circle(cx, y0 + h / 2.0, w / 2.0)
        elif kinds[i] in ("start", "end"):
            fig.rect(x, y0, w, h, r=min(h / 2.0, 18.0))
        else:
            fig.rect(x, y0, w, h)
        fig.text_lines(cx, y0 + h / 2.0, b["lines"], b["size"])

    def bottom(i):
        return boxes[i]["y"] + boxes[i]["h"]

    def node_id(i):
        return num_str(steps[i].get("numeral")) or "step%d" % (i + 1)
    for i in range(n):
        b = boxes[i]
        fig.nodes.append({"id": node_id(i), "label": steps[i].get("label", ""),
                          "numeral": num_str(steps[i].get("numeral")) or None, "parent": None, "container": False,
                          "box": [b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]]})

    # --- sequential connectors
    used_bottom = set()
    for a, idx in seq_from.items():
        _, bdst, lab = edges[idx]
        p0 = (cx, bottom(a))
        p1 = (cx, boxes[bdst]["y"])
        fig.line([p0, p1], arrow_end=True)
        fig.edges.append({"from": node_id(a), "to": node_id(bdst), "label": lab, "pts": [p0, p1]})
        used_bottom.add(a)
        if lab:
            fig.text(cx + 6, p0[1] + TEXT_EDGE * CAP_RATIO + 4, lab, TEXT_EDGE, kind="label")

    # --- side edges via channels on the left
    col_left = min(b["x"] for b in boxes)
    routes = []
    used_left = set()
    for idx in side:
        a, bdst, lab = edges[idx]
        ba = boxes[a]
        if a not in used_left:
            used_left.add(a)
            ex = (cx - ba["w"] / 2.0, ba["y"] + ba["h"] / 2.0)
            mode = "left"
        else:
            ex = (cx, bottom(a))
            mode = "bottom"
            used_bottom.add(a)
        merge_y = boxes[bdst]["y"] - (14.0 if bdst > 0 else 15.0)
        if bdst > 0:
            # middle of the gap above the target
            merge_y = (bottom(bdst - 1) + boxes[bdst]["y"]) / 2.0 + 3.0
        y_ex = ex[1] + (14.0 if mode == "bottom" else 0.0)
        routes.append({"a": a, "b": bdst, "lab": lab, "ex": ex, "mode": mode, "y_ex": y_ex,
                       "merge": merge_y, "span": (min(y_ex, merge_y), max(y_ex, merge_y))})
    routes.sort(key=lambda r: r["span"][1] - r["span"][0])
    chans = []  # list of lists of spans
    for r in routes:
        k = 0
        while True:
            if k == len(chans):
                chans.append([])
            if all(r["span"][1] < s[0] - 4 or r["span"][0] > s[1] + 4 for s in chans[k]):
                chans[k].append(r["span"])
                r["k"] = k
                break
            k += 1
    has_seq_into = set(edges[idx][1] for idx in seq_from.values())
    stubbed = set()
    for r in routes:
        xk = col_left - 24.0 - r["k"] * 18.0
        ex = r["ex"]
        pts = [ex]
        if r["mode"] == "bottom":
            pts.append((ex[0], r["y_ex"]))
        pts += [(xk, r["y_ex"]), (xk, r["merge"]), (cx, r["merge"])]
        fig.line(pts)
        full = list(pts)
        if r["b"] not in has_seq_into and r["b"] not in stubbed:
            stubbed.add(r["b"])
            fig.line([(cx, r["merge"]), (cx, boxes[r["b"]]["y"])], arrow_end=True)
            full.append((cx, boxes[r["b"]]["y"]))
        fig.edges.append({"from": node_id(r["a"]), "to": node_id(r["b"]), "label": r["lab"], "pts": full})
        if r["lab"]:
            if r["mode"] == "left":
                fig.text(ex[0] - 4, ex[1] - 5, r["lab"], TEXT_EDGE, anchor="end")
            else:
                fig.text(ex[0] + 6, ex[1] + TEXT_EDGE * CAP_RATIO + 3, r["lab"], TEXT_EDGE)

    # --- numerals on the right with short lead lines
    for i in range(n):
        k = num_str(steps[i].get("numeral"))
        if not k:
            continue
        b = boxes[i]
        if kinds[i] == "connector":
            r_ = b["w"] / 2.0
            p = (cx + r_ * 0.707, b["y"] + r_ - r_ * 0.707)
            tx = cx + r_ + FC_NUM_DX
            ty = p[1] - 9.0 + NUM_SIZE * DIGIT_RATIO / 2.0
        elif kinds[i] == "decision":
            top = (cx, b["y"])
            right = (cx + b["w"] / 2.0, b["y"] + b["h"] / 2.0)
            t = 0.55
            p = (top[0] + (right[0] - top[0]) * t, top[1] + (right[1] - top[1]) * t)
            tx = right[0] + 6.0
            ty = p[1] - 6.0 + NUM_SIZE * DIGIT_RATIO / 2.0
        else:
            p = (b["x"] + b["w"], b["y"] + min(b["h"] * 0.4, 16.0))
            tx = p[0] + FC_NUM_DX
            ty = p[1] - 9.0 + NUM_SIZE * DIGIT_RATIO / 2.0
        fig.numeral(k, steps[i].get("label", ""), p, (tx, ty))
    return fig


# --------------------------------------------------------------------------- block diagram

BK_MIN_W, BK_MAX_W = 110.0, 210.0
BK_PADX, BK_PADY = 10.0, 9.0
NUM_UP = 16.0     # footprint added above a box for its numeral
NUM_RIGHT = 34.0  # footprint added right of a box for its numeral
CT_PAD = 16.0     # container padding
TRACK = 9.0


class _Box:
    __slots__ = ("id", "x", "y", "w", "h", "kids", "label", "num", "size", "lines", "dash", "parent",
                 "layer", "order", "dummy", "fw", "fh")

    def __init__(self, nid):
        self.id = nid
        self.x = self.y = 0.0
        self.w = self.h = 0.0
        self.kids = []
        self.label = ""
        self.num = ""
        self.size = TEXT_PREF
        self.lines = []
        self.dash = None
        self.parent = None
        self.layer = 0
        self.order = 0
        self.dummy = False
        self.fw = self.fh = 0.0


def _layers(members: List[str], edges: List[Tuple[str, str]]) -> Dict[str, int]:
    """Longest-path layering after DFS cycle removal; sources pulled toward successors."""
    succ = {m: [] for m in members}
    for a, b in edges:
        if a in succ and b in succ and a != b and b not in succ[a]:
            succ[a].append(b)
    # cycle removal
    state = {m: 0 for m in members}
    dag = {m: [] for m in members}

    def dfs(u):
        state[u] = 1
        for v in succ[u]:
            if state[v] == 1:
                dag[v].append(u)   # reverse back edge
            else:
                dag[u].append(v)
                if state[v] == 0:
                    dfs(v)
        state[u] = 2
    for m in members:
        if state[m] == 0:
            dfs(m)
    preds = {m: [] for m in members}
    for a in members:
        for b in dag[a]:
            if a not in preds[b]:
                preds[b].append(a)
    layer = {}

    def L(u, seen=()):
        if u in layer:
            return layer[u]
        if not preds[u]:
            layer[u] = 0
        else:
            layer[u] = 1 + max(L(p) for p in preds[u])
        return layer[u]
    for m in members:
        L(m)
    # pull pure sources down next to their nearest successor
    for m in members:
        if not preds[m] and dag[m]:
            layer[m] = max(layer[m], min(layer[v] for v in dag[m]) - 1)
    return layer


def layout_block(f: dict, case: str) -> Fig:
    """Layered (Sugiyama-style) layout. Containers (nodes named as another node's `parent`) are laid
    out recursively and drawn as enclosing boxes; edges are routed orthogonally through free gaps,
    with dummy slots reserved for edges that skip layers so lines do not run through boxes."""
    fig = Fig(f["id"])
    horiz = (f.get("direction") or "TB").upper() in ("LR", "RL", "H", "HORIZONTAL")
    nodes = f.get("nodes") or []
    if not nodes:
        raise UsageError("%s: block diagram has no nodes" % f["id"])
    boxes = {}   # type: Dict[str, _Box]
    order_in = {}
    for i, nd in enumerate(nodes):
        nid = str(nd.get("id"))
        if nid in boxes:
            raise UsageError("%s: duplicate node id %s" % (f["id"], nid))
        b = _Box(nid)
        b.label = apply_case(nd.get("label", ""), case)
        b.num = num_str(nd.get("numeral"))
        b.parent = str(nd["parent"]) if nd.get("parent") is not None else None
        b.dash = [5, 3] if (nd.get("style") == "dashed") else None
        boxes[nid] = b
        order_in[nid] = i
    for b in list(boxes.values()):
        if b.parent is not None:
            if b.parent not in boxes:
                raise UsageError("%s: node %s has unknown parent %s" % (f["id"], b.id, b.parent))
            boxes[b.parent].kids.append(b.id)
    labels_raw = {str(nd.get("id")): nd.get("label", "") for nd in nodes}
    edges = []
    for e in f.get("edges") or []:
        a, c = str(e.get("from")), str(e.get("to"))
        if a not in boxes or c not in boxes:
            raise UsageError("%s: edge %s -> %s names an unknown node" % (f["id"], a, c))
        edges.append({"from": a, "to": c, "label": apply_case(e.get("label", ""), case),
                      "arrow": (e.get("arrow") or "forward").lower(), "dash": e.get("style") == "dashed"})

    def chain(nid):
        out = [nid]
        while boxes[out[-1]].parent is not None:
            out.append(boxes[out[-1]].parent)
            if len(out) > 50:
                raise UsageError("%s: parent cycle at %s" % (f["id"], nid))
        return out  # leaf .. root

    # an edge between a container and its own descendant cannot be laid out
    for e in edges:
        if e["to"] in chain(e["from"]) or e["from"] in chain(e["to"]):
            raise UsageError("%s: edge %s -> %s joins a box to its own container" % (f["id"], e["from"], e["to"]))

    # leaf sizes: one width per container for a tidy look
    leaves = [b for b in boxes.values() if not b.kids]
    nat = {b.id: min(max(text_width(b.label, TEXT_PREF) + 2 * BK_PADX, BK_MIN_W), BK_MAX_W) for b in leaves}
    groups = {}
    for b in leaves:
        groups.setdefault(b.parent, []).append(b)
    for par, lst in groups.items():
        w = max(nat[b.id] for b in lst)
        for b in lst:
            b.size, b.lines = fit_text(b.label, w - 2 * BK_PADX, max_lines=3)
            b.w = w
            b.h = max(len(b.lines) * b.size * LINE_H + 2 * BK_PADY, 42.0)

    GAP_MAIN = 44.0 if not horiz else 60.0
    GAP_CROSS = 30.0 if not horiz else 34.0

    def XY(m, c):     # (main, cross) -> (x, y)
        return (m, c) if horiz else (c, m)

    def mspan(b):     # main-axis range of a real box
        return (b.x, b.x + b.w) if horiz else (b.y, b.y + b.h)

    def cspan(b):
        return (b.y, b.y + b.h) if horiz else (b.x, b.x + b.w)

    cinfo = {}   # container id -> layout info

    def member_of(nid, cid):
        return next((x for x in chain(nid) if boxes[x].parent == cid and not boxes[x].dummy), None)

    def layout_container(cid):
        members = [k for k in sorted(boxes, key=lambda z: order_in.get(z, 1e9))
                   if boxes[k].parent == cid and not boxes[k].dummy]
        for m in members:
            if boxes[m].kids:
                layout_container(m)
        for m in members:
            b = boxes[m]
            b.fw = b.w + (NUM_RIGHT if b.num else 0.0)
            b.fh = b.h + (NUM_UP if b.num else 0.0)
        me = []  # (member_a, member_b, edge index)
        for ei, e in enumerate(edges):
            ma, mb = member_of(e["from"], cid), member_of(e["to"], cid)
            if ma and mb and ma != mb:
                me.append((ma, mb, ei))
        lay = _layers(members, [(a, c) for a, c, _ in me])
        nl = (max(lay.values()) + 1) if lay else 1
        rows = [[] for _ in range(nl)]
        for m in members:
            rows[lay[m]].append(m)
        chains = {}
        adj = []
        for (a, c, ei) in me:
            la, lc = lay[a], lay[c]
            if la == lc:
                continue
            lo_n, hi_n = (a, c) if la < lc else (c, a)
            l1, l2 = min(la, lc), max(la, lc)
            prev = lo_n
            dl = {}
            for L_ in range(l1 + 1, l2):
                did = "__d%d_%d" % (ei, L_)
                d = _Box(did)
                d.dummy = True
                d.parent = cid
                d.w = d.fw = 14.0
                d.h = d.fh = 0.0
                boxes[did] = d
                lay[did] = L_
                rows[L_].append(did)
                adj.append((prev, did))
                dl[L_] = did
                prev = did
            adj.append((prev, hi_n))
            chains[ei] = dl
        pos = {}
        for r in rows:
            for i, m in enumerate(r):
                pos[m] = i
        nbr = {}
        for (u, v) in adj:
            nbr.setdefault(u, []).append(v)
            nbr.setdefault(v, []).append(u)
        for _ in range(8):
            for li in list(range(1, nl)) + list(range(nl - 2, -1, -1)):
                r = rows[li]
                key = {}
                for m in r:
                    ns = [x for x in nbr.get(m, []) if lay.get(x) != li]
                    key[m] = (sum(pos[x] for x in ns) / float(len(ns))) if ns else pos[m]
                r.sort(key=lambda m: (key[m], pos[m]))
                for i, m in enumerate(r):
                    pos[m] = i

        def fmain(b):
            return b.fw if horiz else b.fh

        def fcross(b):
            return b.fh if horiz else b.fw
        layer_main = [max([fmain(boxes[m]) for m in r] + [0.0]) for r in rows]
        cpos = {}
        widths = []
        for r in rows:
            c = 0.0
            for m in r:
                cpos[m] = c + fcross(boxes[m]) / 2.0
                c += fcross(boxes[m]) + GAP_CROSS
            widths.append(max(c - GAP_CROSS, 0.0))
        wmax = max(widths + [0.0])
        for li, r in enumerate(rows):
            for m in r:
                cpos[m] += (wmax - widths[li]) / 2.0
        for _ in range(10):
            for li in range(nl):
                r = rows[li]
                desired = {}
                for m in r:
                    ns = [x for x in nbr.get(m, []) if x in cpos]
                    desired[m] = (sum(cpos[x] for x in ns) / float(len(ns))) if ns else cpos[m]
                fw_, bw_ = {}, {}
                last = -1e9
                for m in r:
                    half = fcross(boxes[m]) / 2.0
                    fw_[m] = max(desired[m], last + half)
                    last = fw_[m] + half + GAP_CROSS
                last = 1e9
                for m in reversed(r):
                    half = fcross(boxes[m]) / 2.0
                    bw_[m] = min(desired[m], last - half)
                    last = bw_[m] - half - GAP_CROSS
                for m in r:
                    cpos[m] = (fw_[m] + bw_[m]) / 2.0
                last = -1e9
                for m in r:
                    half = fcross(boxes[m]) / 2.0
                    if cpos[m] - half < last:
                        cpos[m] = last + half
                    last = cpos[m] + half + GAP_CROSS
        # gap sizes between consecutive layers: base + tracks + label room
        gaps = []
        for li in range(nl - 1):
            ntr, nlab = 0, 0
            for (a, c, ei) in me:
                l1, l2 = sorted((lay[a], lay[c]))
                if l1 <= li < l2:
                    ntr += 1
                    if edges[ei]["label"] and (li == l2 - 1):
                        nlab = 1
            extra = max(ntr - 1, 0) * TRACK
            if nlab:
                extra += (TEXT_EDGE * 1.6) if not horiz else 50.0
            gaps.append(GAP_MAIN + extra)
        mstart = []
        acc = 0.0
        for li in range(nl):
            mstart.append(acc)
            acc += layer_main[li] + (gaps[li] if li < nl - 1 else 0.0)
        minc = min([cpos[m] - fcross(boxes[m]) / 2.0 for m in cpos] + [0.0])
        for li, r in enumerate(rows):
            for m in r:
                b = boxes[m]
                m0 = mstart[li] + (layer_main[li] - fmain(b)) / 2.0
                c0 = cpos[m] - fcross(b) / 2.0 - minc
                fx, fy = XY(m0, c0)
                b.x = fx
                b.y = fy + (NUM_UP if b.num else 0.0)
        head = 0.0
        if cid is not None:
            c = boxes[cid]
            allb = [boxes[m] for m in lay]
            x1 = max([bb.x + bb.fw for bb in allb] + [0.0])
            y1 = max([bb.y + bb.h for bb in allb] + [0.0])
            size, lines = fit_text(c.label, max(x1, 140.0), max_lines=2)
            c.size, c.lines = size, lines
            head = len(lines) * size * LINE_H + 12.0
            c.w = max(x1, block_w(lines, size) + 4.0) + 2 * CT_PAD
            c.h = y1 + 2 * CT_PAD + head
            for m in lay:
                boxes[m].x += CT_PAD
                boxes[m].y += CT_PAD + head
        cinfo[cid] = {"lay": lay, "rows": rows, "mstart": mstart, "layer_main": layer_main,
                      "gaps": gaps, "chains": chains, "head": head, "me": me}

    layout_container(None)

    def absolutize(cid, ox, oy):
        for k, b in list(boxes.items()):
            if b.parent == cid:
                b.x += ox
                b.y += oy
                if b.kids and not b.dummy:
                    absolutize(k, b.x, b.y)
    absolutize(None, 0.0, 0.0)

    def origin_main(cid):
        if cid is None:
            return 0.0
        c = boxes[cid]
        return (c.x + CT_PAD) if horiz else (c.y + CT_PAD + cinfo[cid]["head"])

    def gap_range(cid, gi):
        ci = cinfo[cid]
        o = origin_main(cid)
        g0 = o + ci["mstart"][gi] + ci["layer_main"][gi]
        g1 = o + ci["mstart"][gi + 1]
        return g0, g1

    def lca(a, c):
        ca, cc = chain(a), chain(c)
        for x in ca[1:] + [None]:
            if x is None or x in cc[1:]:
                # x is the first ancestor of a (excluding a) that also contains c
                pass
        sa = set(ca[1:])
        for x in cc[1:]:
            if x in sa:
                return x
        return None

    def cross_center(b):
        s = cspan(b)
        return (s[0] + s[1]) / 2.0

    # ---- plan routes: sides, waypoints (dummy crosses), gap jogs
    plans = []
    for ei, e in enumerate(edges):
        A, B = boxes[e["from"]], boxes[e["to"]]
        L = lca(e["from"], e["to"])
        ci = cinfo[L]
        ma, mb = member_of(e["from"], L), member_of(e["to"], L)
        la, lb = ci["lay"][ma], ci["lay"][mb]
        if la == lb:
            sa = "chi" if cross_center(B) > cross_center(A) else "clo"
            sb = "clo" if sa == "chi" else "chi"
            plans.append({"ei": ei, "L": L, "same": True, "sa": sa, "sb": sb, "first": cross_center(B),
                          "lastc": cross_center(A)})
            continue
        step = 1 if lb > la else -1
        dl = ci["chains"].get(ei, {})
        way = []   # list of (gap index, next cross)
        l = la
        while l != lb:
            nxt = l + step
            gi = min(l, nxt)
            if nxt == lb:
                way.append((gi, None))
            else:
                d = boxes[dl[nxt]]
                way.append((gi, cross_center(d)))
            l = nxt
        first = way[0][1] if way[0][1] is not None else cross_center(B)
        lastc = way[-2][1] if len(way) >= 2 and way[-2][1] is not None else cross_center(A)
        plans.append({"ei": ei, "L": L, "same": False, "sa": "hi" if step > 0 else "lo",
                      "sb": "lo" if step > 0 else "hi", "way": way, "first": first, "lastc": lastc})

    # ports spread along each side, ordered by where the line goes next
    sides = {}
    for p in plans:
        e = edges[p["ei"]]
        sides.setdefault((e["from"], p["sa"]), []).append((p["ei"], p["first"]))
        sides.setdefault((e["to"], p["sb"]), []).append((p["ei"], p["lastc"]))
    port = {}
    for (bid, sd), lst in sides.items():
        b = boxes[bid]
        if sd in ("hi", "lo"):
            c0, c1 = cspan(b)
            lst.sort(key=lambda t: t[1])
            lo_ = c0 + (c1 - c0) * 0.18
            # keep clear of the numeral lead line at the top-right corner (TB) / top edge (LR)
            hi_ = c1 - (c1 - c0) * (0.3 if (b.num and not horiz and sd == "lo") else 0.18)
        else:
            c0, c1 = mspan(b)
            lst.sort(key=lambda t: t[1])
            lo_ = c0 + (c1 - c0) * 0.3
            hi_ = c1 - (c1 - c0) * 0.3
        k = len(lst)
        for i, (ei, _) in enumerate(lst):
            if k == 1:
                v = min(max((c0 + c1) / 2.0, lo_), hi_)
            else:
                v = lo_ + (hi_ - lo_) * i / (k - 1.0)
            port[(ei, bid, sd)] = v

    # straighten near-miss pairs: when one end is alone on its side and the other end's
    # port lies inside its allowed range, line them up so the edge is one straight run
    side_count = {k: len(v) for k, v in sides.items()}
    for p in plans:
        if p["same"] or len(p["way"]) != 1:
            continue
        e = edges[p["ei"]]
        ka, kb = (p["ei"], e["from"], p["sa"]), (p["ei"], e["to"], p["sb"])
        ca, cb = port[ka], port[kb]
        if abs(ca - cb) < 0.5:
            continue
        ra, rb = cspan(boxes[e["from"]]), cspan(boxes[e["to"]])
        if side_count[(e["from"], p["sa"])] == 1 and ra[0] + 8 <= cb <= ra[1] - 8:
            port[ka] = cb
        elif side_count[(e["to"], p["sb"])] == 1 and rb[0] + 8 <= ca <= rb[1] - 8 - (
                0.3 * (rb[1] - rb[0]) if (boxes[e["to"]].num and not horiz) else 0):
            port[kb] = ca

    # jog tracks per gap
    jogs = {}
    for p in plans:
        if p["same"]:
            continue
        for (gi, _) in p["way"]:
            jogs.setdefault((p["L"], gi), []).append(p["ei"])
    track = {}
    for key, lst in jogs.items():
        g0, g1 = gap_range(*key)
        lst = sorted(set(lst), key=lambda ei: port.get((ei, edges[ei]["from"], next(pp["sa"] for pp in plans if pp["ei"] == ei)), 0.0))
        k = len(lst)
        span = g1 - g0
        for i, ei in enumerate(lst):
            if horiz:
                track[(key, ei)] = g0 + span * (i + 1) / (k + 1.0)
            else:
                # sit near the top of the gap so labels fit beside the final vertical run
                track[(key, ei)] = g0 + min(16.0, span / (k + 1.0)) + i * TRACK

    for p in plans:
        ei = p["ei"]
        e = edges[ei]
        A, B = boxes[e["from"]], boxes[e["to"]]
        if p["same"]:
            # straight across when the two boxes overlap on the main axis, else a Z through the cross gap
            am, bm = mspan(A), mspan(B)
            ac, bc = cspan(A), cspan(B)
            ca = ac[1] if p["sa"] == "chi" else ac[0]
            cb = bc[0] if p["sb"] == "clo" else bc[1]
            lo_, hi_ = max(am[0], bm[0]), min(am[1], bm[1])
            if hi_ - lo_ > 12.0:
                mm = (lo_ + hi_) / 2.0
                pts = [XY(mm, ca), XY(mm, cb)]
            else:
                ma_, mb_ = (am[0] + am[1]) / 2.0, (bm[0] + bm[1]) / 2.0
                cm = (ca + cb) / 2.0
                pts = [XY(ma_, ca), XY(ma_, cm), XY(mb_, cm), XY(mb_, cb)]
                pts = [XY(ma_, ca), XY(ma_, cm)] if False else pts
        else:
            am, bm = mspan(A), mspan(B)
            m_start = am[1] if p["sa"] == "hi" else am[0]
            m_end = bm[0] if p["sb"] == "lo" else bm[1]
            c = port[(ei, e["from"], p["sa"])]
            cb = port[(ei, e["to"], p["sb"])]
            pts = [XY(m_start, c)]
            for (gi, nxt) in p["way"]:
                t = track[((p["L"], gi), ei)]
                nc = cb if nxt is None else nxt
                if abs(nc - c) > 0.5:
                    pts.append(XY(t, c))
                    pts.append(XY(t, nc))
                c = nc
            pts.append(XY(m_end, c))
        e["pts"] = _simplify(pts)
        e["sa"], e["sb"] = p["sa"], p["sb"]

    real = [k for k in boxes if not boxes[k].dummy]

    # ---- reroute any edge that runs through a box that is not one of its ends (F03): the planned route
    # only knows the layers of the lowest common container, so an edge into a nested box could cross a
    # sibling of that box. Such edges get an obstacle-avoiding orthogonal route.
    def num_rect(b):
        w_ = text_width(b.num, NUM_SIZE)
        return (b.x + b.w - 11.0, b.y - 4.0 - NUM_SIZE * DIGIT_RATIO - 1.0, b.x + b.w + 6.0 + w_ + 1.0, b.y + 1.0)

    def head_rect(b):
        return (b.x + 6.0, b.y + 4.0, b.x + 12.0 + block_w(b.lines, b.size), b.y + 10.0 + len(b.lines) * b.size * LINE_H)

    def side_dir(sd, sign):
        """unit vector leaving a box through side sd (hi/lo on the main axis, chi/clo on the cross axis)."""
        main = 1.0 if sd in ("hi", "chi") else -1.0
        if sd in ("hi", "lo"):
            v = XY(main, 0.0)
        else:
            v = XY(0.0, main)
        return (v[0] * sign, v[1] * sign)

    for ei, e in enumerate(edges):
        ok = set(chain(e["from"])) | set(chain(e["to"]))
        segs = list(zip(e["pts"], e["pts"][1:]))
        blockers = [k for k in real if k not in ok and
                    any(seg_hits_rect(a_, b_, (boxes[k].x, boxes[k].y, boxes[k].x + boxes[k].w, boxes[k].y + boxes[k].h),
                                      shrink=0.75) for a_, b_ in segs)]
        if not blockers:
            continue
        common = set(chain(e["from"])[1:]) & set(chain(e["to"])[1:])
        hard, soft = [], []
        CL = 8.0
        for k in real:
            b = boxes[k]
            r = (b.x, b.y, b.x + b.w, b.y + b.h)
            if k in common:          # stay inside shared containers: their borders are walls
                for wall in ((r[0], r[1], r[2], r[1]), (r[0], r[3], r[2], r[3]), (r[0], r[1], r[0], r[3]),
                             (r[2], r[1], r[2], r[3])):
                    hard.append((wall[0] - CL + 1, wall[1] - CL + 1, wall[2] + CL - 1, wall[3] + CL - 1))
                hard.append(head_rect(b))
            elif k in ok and k not in (e["from"], e["to"]):
                hard.append(head_rect(b))   # enclosing container of one end: may cross its border once
            else:
                hard.append((r[0] - CL + 1, r[1] - CL + 1, r[2] + CL - 1, r[3] + CL - 1))
            if b.num:
                soft.append(num_rect(b))
        A_, B_ = boxes[e["from"]], boxes[e["to"]]
        P0, P1 = e["pts"][0], e["pts"][-1]
        d0 = side_dir(e["sa"], 1.0)
        d1 = side_dir(e["sb"], -1.0)       # direction of travel when arriving at B
        S0 = (P0[0] + d0[0] * (CL + 2), P0[1] + d0[1] * (CL + 2))
        S1 = (P1[0] - d1[0] * (CL + 2), P1[1] - d1[1] * (CL + 2))
        others = [sg for j, e2 in enumerate(edges) if j != ei for sg in zip(e2["pts"], e2["pts"][1:])]
        route = _route_orthogonal(S0, d0, S1, d1, hard, soft, others, CL)
        if route is None:
            continue
        e["pts"] = _simplify([P0] + route + [P1])

    # ---- draw: containers first (outermost), then leaves, edges, numerals
    def depth(k):
        return len(chain(k))
    for k in sorted(real, key=lambda z: (depth(z), order_in.get(z, 0))):
        b = boxes[k]
        fig.rect(b.x, b.y, b.w, b.h, lw=LW, dash=b.dash)
        if b.kids:
            lh = b.size * LINE_H
            for i, ln in enumerate(b.lines):
                fig.text(b.x + 9.0, b.y + 8.0 + i * lh + b.size * CAP_RATIO + 1.0, ln, b.size)
        else:
            fig.text_lines(b.x + b.w / 2.0, b.y + b.h / 2.0, b.lines, b.size)
    obstacles = []   # rects that labels must not touch
    for k in real:
        b = boxes[k]
        if b.kids:   # only the container border is an obstacle
            obstacles += [(b.x - 1, b.y - 1, b.x + b.w + 1, b.y + 1), (b.x - 1, b.y + b.h - 1, b.x + b.w + 1, b.y + b.h + 1),
                          (b.x - 1, b.y - 1, b.x + 1, b.y + b.h + 1), (b.x + b.w - 1, b.y - 1, b.x + b.w + 1, b.y + b.h + 1)]
            tb = (b.x + 9.0, b.y + 6.0, b.x + 9.0 + block_w(b.lines, b.size), b.y + 10.0 + len(b.lines) * b.size * LINE_H)
            obstacles.append(tb)
        else:
            obstacles.append((b.x, b.y, b.x + b.w, b.y + b.h))
        if b.num:
            obstacles.append((b.x + b.w - 12, b.y - NUM_UP - 2, b.x + b.w + NUM_RIGHT, b.y))
    segs_all = []
    for e in edges:
        pts = e["pts"]
        for a_, b_ in zip(pts, pts[1:]):
            segs_all.append((min(a_[0], b_[0]) - 0.6, min(a_[1], b_[1]) - 0.6, max(a_[0], b_[0]) + 0.6, max(a_[1], b_[1]) + 0.6))
    for e in edges:
        pts = e["pts"]
        a_end = e["arrow"] in ("forward", "both")
        a_start = e["arrow"] in ("both", "backward")
        fig.line(pts, lw=LW, dash=[5, 3] if e["dash"] else None, arrow_end=a_end, arrow_start=a_start)
    containers_ = [k for k in real if boxes[k].kids]
    for e in edges:
        if not e["label"]:
            continue
        pts = e["pts"]
        segs = list(zip(pts, pts[1:]))
        lab = e["label"]
        size = TEXT_EDGE
        tw_ = text_width(lab, size)
        asc, desc = size * 0.76, size * 0.24
        # F35: anchor the label on the longest run of the connector that stays inside one container,
        # at its midpoint, beside the line (then at its thirds if the midpoint is taken)
        runs = []
        for a_, b_ in segs:
            vert_ = abs(a_[0] - b_[0]) < 0.5
            ts = [0.0, 1.0]
            for kc in containers_:
                cb = boxes[kc]
                for (bx0, by0, bx1, by1) in ((cb.x, cb.y, cb.x + cb.w, cb.y), (cb.x, cb.y + cb.h, cb.x + cb.w, cb.y + cb.h),
                                             (cb.x, cb.y, cb.x, cb.y + cb.h), (cb.x + cb.w, cb.y, cb.x + cb.w, cb.y + cb.h)):
                    if vert_ and abs(by0 - by1) < 0.01 and bx0 < a_[0] < bx1 and min(a_[1], b_[1]) < by0 < max(a_[1], b_[1]):
                        ts.append((by0 - a_[1]) / (b_[1] - a_[1]))
                    elif not vert_ and abs(bx0 - bx1) < 0.01 and by0 < a_[1] < by1 and \
                            min(a_[0], b_[0]) < bx0 < max(a_[0], b_[0]):
                        ts.append((bx0 - a_[0]) / (b_[0] - a_[0]))
            ts = sorted(set(ts))
            for t0, t1 in zip(ts, ts[1:]):
                p0 = (a_[0] + (b_[0] - a_[0]) * t0, a_[1] + (b_[1] - a_[1]) * t0)
                p1 = (a_[0] + (b_[0] - a_[0]) * t1, a_[1] + (b_[1] - a_[1]) * t1)
                runs.append((abs(p1[0] - p0[0]) + abs(p1[1] - p0[1]), p0, p1, vert_))
        runs.sort(key=lambda r_: -r_[0])
        cands = []
        for frac in (0.5, 0.33, 0.67):
            for ln_, p0, p1, vert_ in runs[:3]:
                mx = p0[0] + (p1[0] - p0[0]) * frac
                my = p0[1] + (p1[1] - p0[1]) * frac
                if vert_:
                    cands.append((mx + 6.0, my + size * CAP_RATIO / 2.0, "start"))
                    cands.append((mx - 6.0, my + size * CAP_RATIO / 2.0, "end"))
                else:
                    cands.append((mx, my - 5.0, "middle"))
                    cands.append((mx, my + 5.0 + asc, "middle"))
        if not cands:
            cands.append(((pts[0][0] + pts[-1][0]) / 2.0, (pts[0][1] + pts[-1][1]) / 2.0 - 5.0, "middle"))

        def rect_of(c):
            x, y, an = c
            x0 = x - tw_ / 2.0 if an == "middle" else (x - tw_ if an == "end" else x)
            return (x0 - 2, y - asc - 2, x0 + tw_ + 2, y + desc + 2)

        def hits(r):
            n_ = 0
            for o in obstacles + segs_all:
                if r[0] < o[2] and o[0] < r[2] and r[1] < o[3] and o[1] < r[3]:
                    n_ += 1
            return n_
        best = min(cands, key=lambda c: (hits(rect_of(c)), cands.index(c)))
        fig.text(best[0], best[1], lab, size, anchor=best[2])
        obstacles.append(rect_of(best))
        fig.edge_labels.append({"edge": edges.index(e), "text": lab, "box": list(rect_of(best))})
    for k in sorted(real, key=lambda z: order_in.get(z, 1e9)):
        b = boxes[k]
        if not b.num:
            continue
        p = (b.x + b.w - 10.0, b.y)
        fig.numeral(b.num, labels_raw.get(k, ""), p, (b.x + b.w + 6.0, b.y - 4.0))
    for k in sorted(real, key=lambda z: order_in.get(z, 1e9)):
        b = boxes[k]
        fig.nodes.append({"id": k, "label": labels_raw.get(k, ""), "numeral": b.num or None, "parent": b.parent,
                          "container": bool(b.kids), "box": [b.x, b.y, b.x + b.w, b.y + b.h]})
    for e in edges:
        fig.edges.append({"from": e["from"], "to": e["to"], "label": e["label"], "pts": list(e["pts"])})
    return fig


def _route_orthogonal(S0, d0, S1, d1, hard, soft, others, clear):
    """Shortest orthogonal path S0 -> S1 (A* on the grid of obstacle edges +/- clear and the gaps between
    them) that never enters a `hard` rect. It leaves S0 heading d0 and should arrive heading d1. Costs:
    length, 24 per bend, 150 per `soft` rect crossed (numerals and their lead lines), and running along or
    across `others` (segments of other connectors). Returns [S0, ..., S1] or None."""
    import heapq
    xs, ys = {round(S0[0], 2), round(S1[0], 2)}, {round(S0[1], 2), round(S1[1], 2)}
    for r in hard:
        xs.update((round(r[0] - 1.0, 2), round(r[2] + 1.0, 2)))
        ys.update((round(r[1] - 1.0, 2), round(r[3] + 1.0, 2)))
    for r in soft:   # pass numerals with some air, not touching
        xs.update((round(r[0] - clear * 0.6, 2), round(r[2] + clear * 0.6, 2)))
        ys.update((round(r[1] - clear * 0.6, 2), round(r[3] + clear * 0.6, 2)))
    lo_x, hi_x = min(xs) - 3 * clear, max(xs) + 3 * clear
    lo_y, hi_y = min(ys) - 3 * clear, max(ys) + 3 * clear
    xs.update((lo_x, hi_x))
    ys.update((lo_y, hi_y))
    for coords in (xs, ys):
        srt = sorted(coords)
        coords.update(round((a + b) / 2.0, 2) for a, b in zip(srt, srt[1:]) if b - a > 2 * clear)
    xs, ys = sorted(xs), sorted(ys)
    xi = {v: i for i, v in enumerate(xs)}
    yi = {v: i for i, v in enumerate(ys)}

    def inside(x, y, rects):
        return any(r[0] < x < r[2] and r[1] < y < r[3] for r in rects)

    def seg_cost(a, b):
        for r in hard:
            if seg_hits_rect(a, b, r):
                return None
        c = abs(a[0] - b[0]) + abs(a[1] - b[1])
        for r in soft:
            if seg_hits_rect(a, b, r):
                c += 150.0
        vert = abs(a[0] - b[0]) < 0.01
        for p, q in others:
            if vert and abs(p[0] - q[0]) < 0.01 and abs(p[0] - a[0]) < 3.0:
                ov = min(max(a[1], b[1]), max(p[1], q[1])) - max(min(a[1], b[1]), min(p[1], q[1]))
                if ov > 0:
                    c += 4.0 * ov
            elif not vert and abs(p[1] - q[1]) < 0.01 and abs(p[1] - a[1]) < 3.0:
                ov = min(max(a[0], b[0]), max(p[0], q[0])) - max(min(a[0], b[0]), min(p[0], q[0]))
                if ov > 0:
                    c += 4.0 * ov
            elif seg_hits_rect(a, b, (min(p[0], q[0]) - 0.5, min(p[1], q[1]) - 0.5,
                                      max(p[0], q[0]) + 0.5, max(p[1], q[1]) + 0.5)):
                c += 10.0
        return c
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def dir_index(v):
        return dirs.index((int(round(v[0])), int(round(v[1]))))
    start = (xi[round(S0[0], 2)], yi[round(S0[1], 2)])
    goal = (xi[round(S1[0], 2)], yi[round(S1[1], 2)])
    if inside(S0[0], S0[1], hard) or inside(S1[0], S1[1], hard):
        return None
    k0, k1 = dir_index(d0), dir_index(d1)
    BEND = 24.0
    best = {(start, k0): 0.0}
    prev = {}
    heap = [(abs(S0[0] - S1[0]) + abs(S0[1] - S1[1]), 0.0, start, k0)]
    done = None
    while heap:
        f, g, node, k = heapq.heappop(heap)
        if g > best.get((node, k), 1e18) + 1e-9:
            continue
        if node == goal:
            done = (node, k)
            break
        for nk, (dx, dy) in enumerate(dirs):
            if (dx, dy) == (-dirs[k][0], -dirs[k][1]):
                continue
            ni, nj = node[0] + dx, node[1] + dy
            if not (0 <= ni < len(xs) and 0 <= nj < len(ys)):
                continue
            a = (xs[node[0]], ys[node[1]])
            b = (xs[ni], ys[nj])
            if inside(b[0], b[1], hard):
                continue
            c = seg_cost(a, b)
            if c is None:
                continue
            ng = g + c + (BEND if nk != k else 0.0)
            if (ni, nj) == goal and nk != k1:
                ng += BEND          # arriving sideways needs one more bend into the box
            key = ((ni, nj), nk)
            if ng < best.get(key, 1e18) - 1e-9:
                best[key] = ng
                prev[key] = (node, k)
                h = abs(b[0] - S1[0]) + abs(b[1] - S1[1])
                heapq.heappush(heap, (ng + h, ng, (ni, nj), nk))
    if done is None:
        return None
    path = []
    cur = done
    while True:
        path.append((xs[cur[0][0]], ys[cur[0][1]]))
        if cur == (start, k0):
            break
        cur = prev[cur]
    path.reverse()
    return path


def _simplify(pts):
    out = []
    for p in pts:
        p = (round(p[0], 3), round(p[1], 3))
        if out and abs(out[-1][0] - p[0]) < 0.01 and abs(out[-1][1] - p[1]) < 0.01:
            continue
        out.append(p)
    # drop collinear midpoints
    res = []
    for p in out:
        while len(res) >= 2:
            a, b = res[-2], res[-1]
            if (abs(a[0] - b[0]) < 0.01 and abs(b[0] - p[0]) < 0.01) or (abs(a[1] - b[1]) < 0.01 and abs(b[1] - p[1]) < 0.01):
                res.pop()
            else:
                break
        res.append(p)
    return res


# --------------------------------------------------------------------------- sequence diagram

def layout_sequence(f: dict, case: str) -> Fig:
    fig = Fig(f["id"])
    parts = f.get("participants") or f.get("lifelines") or []
    msgs = f.get("messages") or []
    if not parts:
        raise UsageError("%s: sequence diagram has no participants" % f["id"])
    idx = {str(p.get("id")): i for i, p in enumerate(parts)}
    compact = bool(f.get("_compact"))
    head_wrap = 78.0 if compact else 96.0
    self_wrap = 72.0 if compact else 120.0
    heads = []
    for p in parts:
        lab = apply_case(p.get("label", ""), case)
        size, lines = fit_text(lab, head_wrap, max_lines=3)
        w = max(block_w(lines, size) + 2 * (7.0 if compact else BK_PADX), 70.0 if compact else 80.0)
        h = max(len(lines) * size * LINE_H + 2 * BK_PADY, 40.0)
        heads.append({"w": w, "h": h, "size": size, "lines": lines, "num": num_str(p.get("numeral")),
                      "label": p.get("label", "")})
    n = len(parts)
    # spacing between adjacent lifelines
    sp = [0.0] * max(n - 1, 0)
    for i in range(n - 1):
        # head numerals sit above the box tops, so neighbours only need a plain gap
        sp[i] = max(heads[i]["w"] / 2.0 + heads[i + 1]["w"] / 2.0 + (16.0 if compact else 24.0), 90.0)
    mlines = []
    for m in msgs:
        a, b = str(m.get("from")), str(m.get("to"))
        if a not in idx or b not in idx:
            raise UsageError("%s: message %s -> %s names an unknown participant" % (f["id"], a, b))
        lab = apply_case(m.get("label", ""), case)
        mlines.append((idx[a], idx[b], lab, m))
    for (ia, ib, lab, m) in mlines:
        lo, hi = sorted((ia, ib))
        if lo == hi:
            if lo < n - 1:
                _, sl = fit_text(lab, self_wrap, pref=TEXT_EDGE, max_lines=3)
                sp[lo] = max(sp[lo], block_w(sl, TEXT_EDGE) + 18.0, 34.0 + 16.0 + 30.0 + 10.0)
            continue
        need = text_width(lab, TEXT_EDGE) + 24.0
        if compact:   # allow two lines over the arrow
            longest = max([text_width(w_, TEXT_EDGE) for w_ in lab.split()] + [0.0])
            need = min(need, max(longest, text_width(lab, TEXT_EDGE) / 2.0 + 14.0) + 24.0)
        have = sum(sp[lo:hi])
        if have < need:
            extra = (need - have) / (hi - lo)
            for k in range(lo, hi):
                sp[k] += extra
    xs = [0.0]
    for s in sp:
        xs.append(xs[-1] + s)
    head_h = max(h["h"] for h in heads)
    top = NUM_UP
    for i, h in enumerate(heads):
        h["h"] = head_h          # one height for every head box
        x0 = xs[i] - h["w"] / 2.0
        y0 = top
        fig.rect(x0, y0, h["w"], h["h"])
        fig.text_lines(xs[i], y0 + h["h"] / 2.0, h["lines"], h["size"])
        h["box"] = (x0, y0)
    compact = bool(f.get("_compact"))
    y = top + head_h + (20.0 if compact else 30.0)
    row_gap = 18.0 if compact else 26.0
    row = []
    for (ia, ib, lab, m) in mlines:
        size, lines = fit_text(lab, max(abs(xs[ib] - xs[ia]) - 20.0, 60.0) if ia != ib else self_wrap,
                               pref=TEXT_EDGE, max_lines=2 if ia != ib else 3)
        lh = size * LINE_H
        y += len(lines) * lh + 4.0
        dashed = (m.get("kind") or "").lower() in ("return", "reply", "response", "async_return")
        mnum = num_str(m.get("numeral"))
        if ia == ib:
            # self message: label above the loop (like other messages), numeral right of the loop
            x = xs[ia]
            for k, ln in enumerate(lines):
                fig.text(x + 5.0, y - 5.0 - (len(lines) - 1 - k) * lh, ln, size)
            pts = [(x, y), (x + 34.0, y), (x + 34.0, y + 20.0), (x, y + 20.0)]
            fig.line(pts, dash=[5, 3] if dashed else None, arrow_end=True)
            if mnum:
                fig.numeral(mnum, m.get("label", ""), (x + 34.0, y + 10.0),
                            (x + 34.0 + 16.0, y + 10.0 - 7.0 + NUM_SIZE * DIGIT_RATIO / 2.0))
            y += 20.0 + row_gap
        else:
            x0, x1 = xs[ia], xs[ib]
            for k, ln in enumerate(lines):
                fig.text((x0 + x1) / 2.0, y - 5.0 - (len(lines) - 1 - k) * lh, ln, size, anchor="middle")
            fig.line([(x0, y), (x1, y)], dash=[5, 3] if dashed else None, arrow_end=True)
            if mnum:
                # keep the numeral strictly between the two lifelines so it never sits on a line, 1.84(p)(3)
                dr = 1.0 if x1 >= x0 else -1.0
                L_ = abs(xs[ia + int(dr)] - x0)   # room up to the next lifeline, not the whole span
                nw = text_width(mnum, NUM_SIZE)
                off = min(max(L_ * 0.3, 10.0), max(L_ - 12.0 - 8.0 - nw, 10.0))
                xm = x0 + dr * off
                fig.numeral(mnum, m.get("label", ""), (xm, y), (xm + 12.0 * dr, y + 22.0),
                            anchor="start" if dr > 0 else "end")
                y += 16.0
            y += row_gap
        row.append(y)
    y_end = y + 6.0
    for i, h in enumerate(heads):
        fig.line([(xs[i], h["box"][1] + h["h"]), (xs[i], y_end)], lw=LW_LEAD + 0.15, dash=[6, 4])
    for i, h in enumerate(heads):
        if h["num"]:
            x0, y0 = h["box"]
            fig.numeral(h["num"], h["label"], (x0 + h["w"] - 10.0, y0), (x0 + h["w"] + 6.0, y0 - 4.0))
    return fig


# --------------------------------------------------------------------------- wireframe

DEVICES = {
    "phone": (200.0, 400.0, 22.0, (12.0, 46.0, 12.0, 40.0)),   # w, h, radius, screen insets l,t,r,b
    "tablet": (300.0, 410.0, 18.0, (18.0, 30.0, 18.0, 30.0)),
    "browser": (400.0, 290.0, 4.0, (0.0, 44.0, 0.0, 0.0)),
    "desktop": (400.0, 290.0, 4.0, (10.0, 10.0, 10.0, 10.0)),
    "watch": (160.0, 190.0, 30.0, (16.0, 16.0, 16.0, 16.0)),
    "screen": (360.0, 260.0, 0.0, (0.0, 0.0, 0.0, 0.0)),
}


def layout_wireframe(f: dict, case: str) -> Fig:
    fig = Fig(f["id"])
    dev = f.get("device") or {}
    if isinstance(dev, str):
        dev = {"kind": dev}
    kind = (dev.get("kind") or "phone").lower()
    W, H, R, ins = DEVICES.get(kind, DEVICES["phone"])
    W = float(dev.get("width_pt", W))
    H = float(dev.get("height_pt", H))
    fig.rect(0, 0, W, H, r=R)
    sx0, sy0, sx1, sy1 = ins[0], ins[1], W - ins[2], H - ins[3]
    if kind in ("phone", "tablet", "desktop", "watch"):
        fig.rect(sx0, sy0, sx1 - sx0, sy1 - sy0, r=4.0 if kind != "watch" else 20.0)
    if kind == "phone":
        fig.line([(W / 2 - 22, 22), (W / 2 + 22, 22)], lw=2.0)
        fig.rect(W / 2 - 30, H - 27, 60, 6, r=3)
    if kind == "browser":
        fig.line([(0, 44), (W, 44)])
        for k in range(3):
            fig.circle(14 + k * 14, 14, 4.2, lw=0.9)
        fig.rect(60, 24, W - 76, 14, r=3, lw=0.9)
    sw, sh = sx1 - sx0, sy1 - sy0
    regions = f.get("regions") or []
    placed = []
    for rg in regions:
        x = sx0 + float(rg.get("x", 0)) * sw
        y = sy0 + float(rg.get("y", 0)) * sh
        w = float(rg.get("w", 0.2)) * sw
        h = float(rg.get("h", 0.1)) * sh
        shape = (rg.get("shape") or "rect").lower()
        if shape == "circle":
            fig.circle(x + w / 2, y + h / 2, min(w, h) / 2)
        elif shape == "button":
            fig.rect(x, y, w, h, r=min(h / 2, 8))
        elif shape == "image":
            fig.rect(x, y, w, h)
            fig.line([(x, y), (x + w, y + h)], lw=0.7)
            fig.line([(x + w, y), (x, y + h)], lw=0.7)
        elif shape == "text":
            k = max(1, int(h // 12))
            for j in range(k):
                yy = y + 6 + j * 12
                fig.line([(x, yy), (x + w * (0.92 if j < k - 1 else 0.6), yy)], lw=0.9)
        else:
            fig.rect(x, y, w, h)
        lab = apply_case(rg.get("label", ""), case)
        if lab and shape not in ("text", "image"):
            size, lines = fit_text(lab, max(w - 8, 10), max_lines=2)
            fits = (block_w(lines, size) <= w - 6) and (len(lines) * size * LINE_H <= h - 4)
            if fits:
                fig.text_lines(x + w / 2, y + h / 2, lines, size)
        placed.append((rg, x, y, w, h))
    # numerals: left/right columns, monotonic in y so lead lines never cross each other
    left = [p for p in placed if num_str(p[0].get("numeral")) and (p[1] + p[3] / 2) < W / 2]
    right = [p for p in placed if num_str(p[0].get("numeral")) and (p[1] + p[3] / 2) >= W / 2]
    for side, lst in (("L", left), ("R", right)):
        lst.sort(key=lambda p: p[2] + p[4] / 2)
        ys = []
        last = -1e9
        for p in lst:
            want = p[2] + p[4] / 2
            v = max(want, last + 20.0)
            ys.append(v)
            last = v
        # push the column up if it overflows the device height
        over = (ys[-1] - (H - 8)) if ys else 0
        if over > 0:
            ys = [v - over for v in ys]
            for i in range(len(ys) - 2, -1, -1):
                ys[i] = min(ys[i], ys[i + 1] - 20.0)
        for p, yv in zip(lst, ys):
            rg, x, y, w, h = p
            if (rg.get("shape") or "").lower() == "text":
                k_ = max(1, int(h // 12))
                j_ = max(0, min(k_ - 2, k_ // 2))
                yy_ = y + 6 + j_ * 12
                target = (x, yy_) if side == "L" else (x + w * 0.92, yy_)
            elif (rg.get("shape") or "").lower() == "circle":
                r_ = min(w, h) / 2
                target = (x + w / 2 - r_, y + h / 2) if side == "L" else (x + w / 2 + r_, y + h / 2)
            else:
                target = (x, y + h / 2) if side == "L" else (x + w, y + h / 2)
            if side == "L":
                fig.numeral(num_str(rg.get("numeral")), rg.get("label", ""), target,
                            (-26.0, yv + NUM_SIZE * DIGIT_RATIO / 2), anchor="end")
            else:
                fig.numeral(num_str(rg.get("numeral")), rg.get("label", ""), target,
                            (W + 26.0, yv + NUM_SIZE * DIGIT_RATIO / 2), anchor="start")
    dn = num_str(dev.get("numeral"))
    if dn:
        fig.numeral(dn, dev.get("label", kind), (W - R * 0.3, R * 0.3 + 2), (W + 14.0, -6.0))
    return fig


# --------------------------------------------------------------------------- graph

def _nice_ticks(lo, hi, n=5):
    if hi <= lo:
        hi = lo + 1.0
    span = hi - lo
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=mag * 10)
    start = math.floor(lo / step) * step
    ticks = []
    v = start
    while True:
        ticks.append(round(v, 10))
        if v >= hi - step * 0.001:
            break
        v += step
    return ticks


def _fmt(v):
    return ("%d" % v) if abs(v - round(v)) < 1e-9 else ("%g" % v)


def layout_graph(f: dict, case: str) -> Fig:
    fig = Fig(f["id"])
    PW, PH = float(f.get("width_pt", 300.0)), float(f.get("height_pt", 210.0))
    kind = (f.get("kind") or f.get("chart") or "line").lower()
    xl = apply_case(f.get("x_label", ""), case)
    yl = apply_case(f.get("y_label", ""), case)
    ox, oy = 0.0, 0.0
    fig.line([(ox, oy), (ox, oy + PH), (ox + PW, oy + PH)])
    series = f.get("series") or []
    if kind == "bar":
        bars = f.get("bars") or []
        if not bars and series:
            bars = [{"label": str(p[0]), "value": p[1]} for p in series[0].get("points", [])]
        vals = [float(b.get("value", 0)) for b in bars] or [1.0]
        yt = _nice_ticks(min(0.0, min(vals)), max(vals))
        y0, y1 = yt[0], yt[-1]
        nb = max(len(bars), 1)
        slot = PW / nb
        max_lines = 1
        for i, b in enumerate(bars):
            v = float(b.get("value", 0))
            bh = (v - y0) / (y1 - y0) * PH
            bx = ox + i * slot + slot * 0.2
            bw = slot * 0.6
            fig.rect(bx, oy + PH - bh, bw, bh)
            if i % 2 == 1:   # hatch alternate bars (spaced lines, 1.84(m))
                k = bx - bh
                while k < bx + bw:
                    xa, ya = max(bx, k), oy + PH - max(0.0, bx - k)
                    xb_, yb = min(bx + bw, k + bh), oy + PH - min(bh, (bx + bw) - k)
                    if xb_ > xa:
                        fig.line([(xa, ya), (xb_, oy + PH - (xb_ - k))], lw=0.6)
                    k += 9.0
            lab = apply_case(b.get("label", ""), case)
            size, lines = fit_text(lab, max(slot - 6, 30), pref=TEXT_EDGE, max_lines=2)
            max_lines = max(max_lines, len(lines))
            for j, ln in enumerate(lines):
                fig.text(bx + bw / 2, oy + PH + 16 + j * size * LINE_H, ln, size, anchor="middle")
            bn = num_str(b.get("numeral"))
            if bn:
                fig.numeral(bn, b.get("label", ""), (bx + bw * 0.75, oy + PH - bh), (bx + bw + 4, oy + PH - bh - 10))
        xt_bottom = oy + PH + 16 + (max_lines - 1) * TEXT_EDGE * LINE_H
    else:
        allx = [float(p[0]) for s in series for p in s.get("points", [])] or [0.0, 1.0]
        ally = [float(p[1]) for s in series for p in s.get("points", [])] or [0.0, 1.0]
        xt = _nice_ticks(min(allx), max(allx))
        yt = _nice_ticks(min(0.0, min(ally)), max(ally))
        x0, x1, y0, y1 = xt[0], xt[-1], yt[0], yt[-1]

        def P(px, py):
            return (ox + (px - x0) / (x1 - x0) * PW, oy + PH - (py - y0) / (y1 - y0) * PH)
        for t in xt:
            X, _ = P(t, y0)
            fig.line([(X, oy + PH), (X, oy + PH + 5)], lw=0.8)
            fig.text(X, oy + PH + 7 + TEXT_EDGE * CAP_RATIO, _fmt(t), TEXT_EDGE, anchor="middle")
        dashes = [None, [6, 3], [2, 2.5], [8, 3, 2, 3]]
        for si, s in enumerate(series):
            pts = [P(float(p[0]), float(p[1])) for p in s.get("points", [])]
            if len(pts) >= 2:
                fig.line(pts, lw=1.3, dash=dashes[si % len(dashes)])
            for (X, Y) in pts:
                if si % 2 == 0:
                    fig.circle(X, Y, 2.6, lw=0.9)
                else:
                    fig.rect(X - 2.6, Y - 2.6, 5.2, 5.2, lw=0.9)
            sn = num_str(s.get("numeral"))
            if sn and pts:
                X, Y = pts[-1] if len(pts) == 1 else pts[int(len(pts) * 0.7)]
                fig.numeral(sn, s.get("label", ""), (X + 2, Y - 2), (X + 22, Y - 16 - si * 4))
        xt_bottom = oy + PH + 7 + TEXT_EDGE * CAP_RATIO + 4
    for t in yt:
        if kind == "bar":
            Y = oy + PH - (t - yt[0]) / (yt[-1] - yt[0]) * PH
        else:
            Y = oy + PH - (t - yt[0]) / (yt[-1] - yt[0]) * PH
        fig.line([(ox - 5, Y), (ox, Y)], lw=0.8)
        fig.text(ox - 8, Y + TEXT_EDGE * CAP_RATIO / 2, _fmt(t), TEXT_EDGE, anchor="end")
    if xl:
        fig.text(ox + PW / 2, xt_bottom + 20, xl, TEXT_EDGE, anchor="middle")
    if yl:
        wmax = max(text_width(_fmt(t), TEXT_EDGE) for t in yt)
        # standard scientific convention allows a rotated ordinate label, 1.84(i)
        fig.text(ox - 16 - wmax, oy + PH / 2, yl, TEXT_EDGE, anchor="middle", rot=90)
    return fig


# --------------------------------------------------------------------------- image (user line art)

def layout_image(f: dict, case: str, base_dir: str, out_dir: str, warnings: List[dict]) -> Fig:
    fig = Fig(f["id"])
    src = f.get("path") or f.get("src")
    if not src:
        raise UsageError("%s: image figure needs 'path'" % f["id"])
    path = src if os.path.isabs(src) else os.path.join(base_dir, src)
    if not os.path.exists(path):
        raise UsageError("%s: image not found: %s" % (f["id"], path))
    W = H = None
    use = path
    try:
        from PIL import Image, ImageOps
        im = Image.open(path)
        im = ImageOps.exif_transpose(im) if hasattr(ImageOps, "exif_transpose") else im
        g = ImageOps.autocontrast(im.convert("L"))
        thr = int(f.get("threshold", 160))
        bw = g.point(lambda v: 255 if v >= thr else 0, mode="1")
        use = os.path.join(out_dir, "%s-lineart.png" % safe_name(f["id"]))
        bw.save(use)
        W, H = bw.size
    except ImportError:
        warnings.append({"level": "WARN", "code": "image-not-converted", "where": f["id"],
                         "message": "Pillow not installed (pip install pillow); image placed as-is - "
                                    "it may contain gray or color, which 1.84(a)(1) does not allow."})
    except Exception as ex:  # noqa
        raise UsageError("%s: cannot read image: %s" % (f["id"], ex))
    if W is None:
        W, H = _png_size(path)
    maxw, maxh = float(f.get("max_width_pt", 360.0)), float(f.get("max_height_pt", 470.0))
    s = min(maxw / W, maxh / H)
    w, h = W * s, H * s
    fig.image(use, 0, 0, w, h)
    marks = f.get("numerals") or f.get("callouts") or []
    left = [m for m in marks if float(m.get("x", 0)) < 0.5]
    right = [m for m in marks if float(m.get("x", 0)) >= 0.5]
    for side, lst in (("L", left), ("R", right)):
        lst.sort(key=lambda m: float(m.get("y", 0)))
        last = -1e9
        for m in lst:
            tx_, ty_ = float(m.get("x", 0)) * w, float(m.get("y", 0)) * h
            yv = max(ty_, last + 20.0)
            last = yv
            if side == "L":
                fig.numeral(num_str(m.get("numeral")), m.get("label", ""), (tx_, ty_),
                            (-22.0, yv + NUM_SIZE * DIGIT_RATIO / 2), anchor="end")
            else:
                fig.numeral(num_str(m.get("numeral")), m.get("label", ""), (tx_, ty_),
                            (w + 22.0, yv + NUM_SIZE * DIGIT_RATIO / 2), anchor="start")
    return fig


def _png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(32)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        import struct
        return struct.unpack(">II", head[16:24])
    raise UsageError("cannot size %s without Pillow (pip install pillow)" % path)


# --------------------------------------------------------------------------- sheets

def sight(sheet_name: str) -> Tuple[float, float, List[float]]:
    W, H = SHEETS[sheet_name]
    x0 = MARGINS_CM["left"] * PT_PER_CM
    y0 = MARGINS_CM["top"] * PT_PER_CM
    x1 = W - MARGINS_CM["right"] * PT_PER_CM
    y1 = H - MARGINS_CM["bottom"] * PT_PER_CM
    return W, H, [x0, y0, x1, y1]


def fig_label(fid: str) -> str:
    s = str(fid).strip()
    up = s.upper()
    if up.startswith("FIG"):
        rest = s[3:].lstrip(". ").strip()
        return "FIG. " + rest
    return "FIG. " + s


def usable(sheet_name: str):
    """Area left for views: the sight minus a safety inset and the sheet-number band at its top."""
    W, H, sg = sight(sheet_name)
    band = SHEETNO_SIZE * 1.0 + 18.0          # sheet number lives at the top of the sight, 1.84(t)
    return (sg[0] + SAFETY_PT, sg[1] + SAFETY_PT + band, sg[2] - SAFETY_PT, sg[3] - SAFETY_PT)


def fit_scale(fig: Fig, sheet_name: str) -> float:
    """Scale at which the figure fills the usable sight (1.0 when it fits as drawn)."""
    ax0, ay0, ax1, ay1 = usable(sheet_name)
    b = fig.bbox()
    return min(1.0, (ax1 - ax0) / max(b[2] - b[0], 1e-6), (ay1 - ay0) / max(b[3] - b[1], 1e-6))


BUDGET_UNITS = {"flowchart": ("steps", "steps"), "block": ("nodes", "boxes"), "sequence": ("messages", "messages"),
                "wireframe": ("regions", "regions"), "graph": ("series", "series"), "image": ("numerals", "callouts")}


def size_budget(ent: dict, sheet_name: str) -> dict:
    """How much of the sight a figure needs at 0.32 cm text, and about how many elements fit (F34)."""
    fig, typ, spec = ent["fig"], ent["type"], ent["spec"]
    ax0, ay0, ax1, ay1 = usable(sheet_name)
    aw, ah = ax1 - ax0, ay1 - ay0
    b = fig.bbox()
    w, h = max(b[2] - b[0], 1e-6), max(b[3] - b[1], 1e-6)
    s_raw = min(aw / w, ah / h)
    mt = fig.min_text()
    s_min = (MIN_TEXT_CM * PT_PER_CM) / (mt * CAP_RATIO) if mt else 0.0
    key, unit = BUDGET_UNITS.get(typ, ("", "elements"))
    items = spec.get(key) or (spec.get("bars") if typ == "graph" else None) or \
        (spec.get("callouts") if typ == "image" else None) or []
    if typ == "block":
        parents = set(str(x.get("parent")) for x in items if x.get("parent") is not None)
        items = [x for x in items if str(x.get("id")) not in parents]   # leaf boxes
    if typ == "flowchart":
        items = [x for x in items if str(x.get("kind") or "").lower() not in ("connector", "off-page", "offpage")]
    count = len(items)
    cap = int(count * s_raw / s_min) if s_min > 0 and count else None
    fits_ = s_raw >= s_min - 1e-6
    s = min(1.0, s_raw)
    out = {"id": ent["id"], "type": typ, "count": count, "unit": unit, "scale": round(s, 2),
           "min_scale": round(min(s_min, 1.0), 2), "fits": fits_, "capacity": cap,
           "width_used": round(w * s / aw, 2), "height_used": round(h * s / ah, 2)}
    if fits_:
        out["message"] = ("%s (%s): %d %s, fits at scale %.2f (%d%% of the sight height, %d%% of its width)%s"
                          % (ent["id"], typ, count, unit, s, round(100 * out["height_used"]),
                             round(100 * out["width_used"]),
                             ("; about %d %s would fit" % (cap, unit)) if cap and cap > count else ""))
    else:
        how = ("split it into partial views joined by connector steps (\"kind\": \"connector\", \"label\": \"A\"), "
               "FIG. nA / nB" if typ == "flowchart" else
               "split system and component views (about 10 boxes per figure)" if typ == "block" else
               "split it into partial views (1.84(h)(2)) or shorten labels")
        out["message"] = ("%s (%s): %d %s need scale %.2f, but 0.32 cm text allows no smaller than %.2f; about %d %s "
                          "fit per view - %s" % (ent["id"], typ, count, unit, s, s_min, cap or 0, unit, how))
    return out


def fits(fig: Fig, sheet_name: str) -> bool:
    ax0, ay0, ax1, ay1 = usable(sheet_name)
    b = fig.bbox()
    s = min(1.0, (ax1 - ax0) / max(b[2] - b[0], 1e-6), (ay1 - ay0) / max(b[3] - b[1], 1e-6))
    return fig.min_text() * s * CAP_RATIO >= MIN_TEXT_CM * PT_PER_CM - 1e-6


def pack(figs: List[dict], sheet_name: str, findings: List[dict]):
    """Place each figure (in order) on sheets. Returns list of sheets: [{figs:[(entry, ox, oy, s)]}]."""
    W, H, sg = sight(sheet_name)
    ax0, ay0, ax1, ay1 = usable(sheet_name)
    aw, ah = ax1 - ax0, ay1 - ay0
    GAP = 34.0
    sheets = []
    cur = []
    cur_h = 0.0
    for ent in figs:
        fig = ent["fig"]
        b = fig.bbox()
        w, h = b[2] - b[0], b[3] - b[1]
        s = min(1.0, aw / w if w > 0 else 1.0, ah / h if h > 0 else 1.0)
        if s < 1.0:
            mt = fig.min_text() * s
            if mt * CAP_RATIO < MIN_TEXT_CM * PT_PER_CM - 1e-6:
                findings.append({"level": "BLOCK", "code": "figure-too-large", "where": ent["id"],
                                 "message": "figure does not fit the sight at 0.32 cm text (needs scale %.2f); "
                                            "split it into partial views (e.g., FIG. 3A / FIG. 3B, 1.84(h)(2)) "
                                            "or shorten labels" % s})
        ent["scale"] = s
        ent["size"] = (w * s, h * s)
        own = bool(ent["spec"].get("own_sheet")) or h * s > ah * 0.62
        if cur and (own or cur_h + GAP + h * s > ah or ent["spec"].get("new_sheet")):
            sheets.append(cur)
            cur, cur_h = [], 0.0
        cur.append(ent)
        cur_h += (GAP if len(cur) > 1 else 0.0) + h * s
        if own:
            sheets.append(cur)
            cur, cur_h = [], 0.0
    if cur:
        sheets.append(cur)
    placed = []
    for sh in sheets:
        total = sum(e["size"][1] for e in sh)
        free = ah - total
        gap = min(free / (len(sh) + 1), 90.0)
        y = ay0 + (ah - total - gap * (len(sh) - 1)) / 2.0
        row = []
        for e in sh:
            b = e["fig"].bbox()
            w, h = e["size"]
            ox = ax0 + (aw - w) / 2.0 - b[0] * e["scale"]
            oy = y - b[1] * e["scale"]
            row.append((e, ox, oy, e["scale"]))
            e["page_bbox"] = [ax0 + (aw - w) / 2.0, y, ax0 + (aw - w) / 2.0 + w, y + h]
            y += h + gap
        placed.append(row)
    return placed, (W, H, sg)


def _tx(ox, oy, s, x, y):
    return (ox + x * s, oy + y * s)


def render_pdf(path: str, placed, geom, findings):
    from reportlab.pdfgen import canvas
    W, H, sg = geom
    # initialFontName keeps reportlab from referencing a non-embedded Helvetica on every page
    c = canvas.Canvas(path, pagesize=(W, H), pageCompression=1, invariant=1,
                      initialFontName=FONT, initialFontSize=NUM_SIZE)
    c.setTitle("Drawings")
    c.setAuthor("")
    c.setCreator("patentassist drawings.py")
    nsheets = len(placed)
    for si, row in enumerate(placed):
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(0, 0, 0)
        # sheet number inside the sight, top center, 1.84(t)
        c.setFont(FONT, SHEETNO_SIZE)
        c.drawCentredString(W / 2.0, H - (sg[1] + SAFETY_PT + SHEETNO_SIZE * CAP_RATIO + 2.0),
                            "%d/%d" % (si + 1, nsheets))
        for (ent, ox, oy, s) in row:
            for it in ent["fig"].items:
                _draw_item(c, it, ox, oy, s, H)
        c.showPage()
    c.save()


def _draw_item(c, it, ox, oy, s, H):
    t = it["t"]

    def P(x, y):
        X, Y = _tx(ox, oy, s, x, y)
        return X, H - Y
    if t in ("line", "poly", "rect", "circle", "curve"):
        c.setLineWidth(max(it.get("lw", LW) * s, 0.5))
        dash = it.get("dash")
        if dash:
            c.setDash([d * s for d in dash], 0)
        else:
            c.setDash([], 0)
        c.setLineCap(0)
        c.setLineJoin(1)
    if t == "line":
        p = c.beginPath()
        x, y = P(*it["pts"][0])
        p.moveTo(x, y)
        for q in it["pts"][1:]:
            x, y = P(*q)
            p.lineTo(x, y)
        c.drawPath(p, stroke=1, fill=0)
    elif t == "poly":
        p = c.beginPath()
        x, y = P(*it["pts"][0])
        p.moveTo(x, y)
        for q in it["pts"][1:]:
            x, y = P(*q)
            p.lineTo(x, y)
        if it.get("closed", True):
            p.close()
        c.drawPath(p, stroke=1, fill=1 if it.get("fill") else 0)
    elif t == "curve":
        a, b1, b2, d = [P(*q) for q in it["pts"]]
        p = c.beginPath()
        p.moveTo(*a)
        p.curveTo(b1[0], b1[1], b2[0], b2[1], d[0], d[1])
        c.drawPath(p, stroke=1, fill=0)
    elif t == "rect":
        x, y = P(it["x"], it["y"] + it["h"])
        w, h = it["w"] * s, it["h"] * s
        if it.get("r"):
            c.roundRect(x, y, w, h, it["r"] * s, stroke=1, fill=0)
        else:
            c.rect(x, y, w, h, stroke=1, fill=0)
    elif t == "circle":
        x, y = P(it["cx"], it["cy"])
        c.circle(x, y, it["r"] * s, stroke=1, fill=0)
    elif t == "text":
        c.setFont(FONT_B if it.get("bold") else FONT, it["size"] * s)
        x, y = P(it["x"], it["y"])
        if it.get("rot"):
            c.saveState()
            c.translate(x, y)
            c.rotate(90)
            _draw_str(c, 0, 0, it)
            c.restoreState()
        else:
            _draw_str(c, x, y, it)
    elif t == "image":
        x, y = P(it["x"], it["y"] + it["h"])
        c.drawImage(it["path"], x, y, it["w"] * s, it["h"] * s, mask=None)


def _draw_str(c, x, y, it):
    a = it.get("anchor", "start")
    if a == "middle":
        c.drawCentredString(x, y, it["s"])
    elif a == "end":
        c.drawRightString(x, y, it["s"])
    else:
        c.drawString(x, y, it["s"])


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def render_svg(path: str, fig: Fig):
    b = fig.bbox()
    pad = 8.0
    x0, y0 = b[0] - pad, b[1] - pad
    w, h = b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg" width="%.2fpt" height="%.2fpt" viewBox="%.2f %.2f %.2f %.2f">'
           % (w, h, x0, y0, w, h),
           '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="#ffffff"/>' % (x0, y0, w, h),
           '<g fill="none" stroke="#000000" stroke-linejoin="round" '
           'font-family="Bitstream Vera Sans, DejaVu Sans, Arial, Helvetica, sans-serif">']
    for it in fig.items:
        t = it["t"]
        dash = ' stroke-dasharray="%s"' % ",".join("%g" % d for d in it["dash"]) if it.get("dash") else ""
        if t == "line":
            d = "M " + " L ".join("%.2f %.2f" % p for p in it["pts"])
            out.append('<path d="%s" stroke-width="%.2f"%s/>' % (d, it["lw"], dash))
        elif t == "poly":
            d = "M " + " L ".join("%.2f %.2f" % p for p in it["pts"]) + (" Z" if it.get("closed", True) else "")
            fill = ' fill="#000000"' if it.get("fill") else ""
            out.append('<path d="%s" stroke-width="%.2f"%s%s/>' % (d, it["lw"], fill, dash))
        elif t == "curve":
            p = it["pts"]
            out.append('<path d="M %.2f %.2f C %.2f %.2f %.2f %.2f %.2f %.2f" stroke-width="%.2f"/>'
                       % (p[0][0], p[0][1], p[1][0], p[1][1], p[2][0], p[2][1], p[3][0], p[3][1], it["lw"]))
        elif t == "rect":
            r = ' rx="%.2f"' % it["r"] if it.get("r") else ""
            out.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f"%s stroke-width="%.2f"%s/>'
                       % (it["x"], it["y"], it["w"], it["h"], r, it["lw"], dash))
        elif t == "circle":
            out.append('<circle cx="%.2f" cy="%.2f" r="%.2f" stroke-width="%.2f"/>'
                       % (it["cx"], it["cy"], it["r"], it["lw"]))
        elif t == "text":
            anchor = {"start": "start", "middle": "middle", "end": "end"}[it.get("anchor", "start")]
            tr = ' transform="rotate(-90 %.2f %.2f)"' % (it["x"], it["y"]) if it.get("rot") else ""
            wt = ' font-weight="bold"' if it.get("bold") else ""
            out.append('<text x="%.2f" y="%.2f" font-size="%.2f" text-anchor="%s" fill="#000000" stroke="none"%s%s>%s</text>'
                       % (it["x"], it["y"], it["size"], anchor, wt, tr, _esc(it["s"])))
        elif t == "image":
            try:
                with open(it["path"], "rb") as fh:
                    data = base64.b64encode(fh.read()).decode("ascii")
                ext = os.path.splitext(it["path"])[1].lower().lstrip(".")
                mime = "image/png" if ext == "png" else "image/jpeg"
                out.append('<image x="%.2f" y="%.2f" width="%.2f" height="%.2f" href="data:%s;base64,%s"/>'
                           % (it["x"], it["y"], it["w"], it["h"], mime, data))
            except OSError:
                pass
    out.append("</g></svg>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


# --------------------------------------------------------------------------- main build

# Every key figures.json may use (references/state-files.md, figures@1). Keys starting with "_" are
# comments and ignored. drawings.py WARNs on anything else, because a misspelled key is silently ignored.
FIGURE_KEYS = {
    "_top": {"schema", "sheet", "text_case", "figures"},
    "_common": {"id", "type", "title", "text_case", "own_sheet", "new_sheet"},
    "flowchart": {"steps"},
    "block": {"nodes", "edges", "direction"},
    "sequence": {"participants", "lifelines", "messages"},
    "wireframe": {"device", "regions"},
    "graph": {"kind", "chart", "width_pt", "height_pt", "x_label", "y_label", "series", "bars"},
    "image": {"path", "src", "threshold", "max_width_pt", "max_height_pt", "numerals", "callouts"},
}
ITEM_KEYS = {   # (figure type, list key) -> keys of each item
    ("flowchart", "steps"): {"numeral", "label", "kind", "next", "next_label", "yes", "no", "yes_label", "no_label"},
    ("block", "nodes"): {"id", "label", "numeral", "parent", "style"},
    ("block", "edges"): {"from", "to", "label", "arrow", "style"},
    ("sequence", "participants"): {"id", "label", "numeral"},
    ("sequence", "lifelines"): {"id", "label", "numeral"},
    ("sequence", "messages"): {"from", "to", "label", "numeral", "kind"},
    ("wireframe", "regions"): {"x", "y", "w", "h", "shape", "label", "numeral"},
    ("graph", "series"): {"label", "numeral", "points"},
    ("graph", "bars"): {"label", "value", "numeral"},
    ("image", "numerals"): {"numeral", "label", "x", "y"},
    ("image", "callouts"): {"numeral", "label", "x", "y"},
}
DEVICE_KEYS = {"kind", "width_pt", "height_pt", "numeral", "label"}
ENUMS = {   # (figure type, list key or "", item key) -> allowed values (lower case)
    ("flowchart", "steps", "kind"): {"step", "process", "io", "action", "start", "end", "terminal", "terminator",
                                     "decision", "connector", "off-page", "offpage", "off_page"},
    ("block", "", "direction"): {"tb", "lr", "rl", "h", "horizontal", "v", "vertical"},
    ("block", "nodes", "style"): {"solid", "dashed"},
    ("block", "edges", "style"): {"solid", "dashed"},
    ("block", "edges", "arrow"): {"forward", "backward", "both", "none"},
    ("sequence", "messages", "kind"): {"call", "sync", "async", "return", "reply", "response", "async_return"},
    ("wireframe", "regions", "shape"): {"rect", "circle", "button", "image", "text"},
    ("graph", "", "kind"): {"line", "bar"},
    ("graph", "", "chart"): {"line", "bar"},
}


def validate_keys(data: dict, findings: List[dict]):
    """WARN on keys drawings.py does not read (F33) and on values outside the documented choices."""
    def warn(where, msg):
        findings.append({"level": "WARN", "code": "unknown-key", "where": where, "message": msg})
    for k in data:
        if not str(k).startswith("_") and k not in FIGURE_KEYS["_top"]:
            warn("figures.json", "unknown top-level key %r is ignored (keys: %s)" % (k, ", ".join(sorted(FIGURE_KEYS["_top"]))))
    for f in data.get("figures") or []:
        if not isinstance(f, dict):
            continue
        fid = str(f.get("id", "?"))
        typ = str(f.get("type") or "").lower()
        allowed = FIGURE_KEYS["_common"] | FIGURE_KEYS.get(typ, set())
        for k in f:
            if not str(k).startswith("_") and k not in allowed:
                warn(fid, "unknown key %r for a %s figure is ignored (keys: %s)" % (k, typ or "?", ", ".join(sorted(allowed))))
        for (t, lk, ik), vals in ENUMS.items():
            if t == typ and lk == "" and f.get(ik) is not None and str(f[ik]).lower() not in vals:
                warn(fid, "%s %r is not one of %s" % (ik, f[ik], ", ".join(sorted(vals))))
        if typ == "wireframe" and isinstance(f.get("device"), dict):
            for k in f["device"]:
                if not str(k).startswith("_") and k not in DEVICE_KEYS:
                    warn(fid, "unknown device key %r is ignored (keys: %s)" % (k, ", ".join(sorted(DEVICE_KEYS))))
        for (t, lk), keys in ITEM_KEYS.items():
            if t != typ or not isinstance(f.get(lk), list):
                continue
            for i, it in enumerate(f[lk], 1):
                if not isinstance(it, dict):
                    continue
                for k in it:
                    if not str(k).startswith("_") and k not in keys:
                        warn(fid, "%s[%d]: unknown key %r is ignored (keys: %s)" % (lk, i, k, ", ".join(sorted(keys))))
                for (t2, lk2, ik), vals in ENUMS.items():
                    if t2 == typ and lk2 == lk and it.get(ik) is not None and str(it[ik]).lower() not in vals:
                        warn(fid, "%s[%d]: %s %r is not one of %s" % (lk, i, ik, it[ik], ", ".join(sorted(vals))))


LAYOUTS = {"flowchart": layout_flowchart, "block": layout_block, "sequence": layout_sequence,
           "wireframe": layout_wireframe, "graph": layout_graph}


def _resolve(path: str, d: str) -> str:
    if os.path.isabs(path) or os.path.exists(path):
        return path
    alt = os.path.join(d, path)
    return alt if os.path.exists(alt) or os.path.isdir(os.path.dirname(alt) or ".") else path


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _audit(d, rec, no_audit):
    if no_audit or not d or not os.path.isdir(d):
        return
    rec = dict(rec)
    rec["ts"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with open(os.path.join(d, "audit.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def build(figures_path: str, out_dir: str, d: str = "patent", no_audit: bool = False) -> dict:
    findings = []  # type: List[dict]
    with open(figures_path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except ValueError as ex:
            raise UsageError("figures.json is not valid JSON: %s" % ex)
    schema = str(data.get("schema", ""))
    if not schema.startswith("patentassist/figures@"):
        raise UsageError("not a patentassist/figures file (schema=%r)" % schema)
    if schema.split("@")[-1].split(".")[0] != "1":
        raise UsageError("unknown figures schema major version: %s" % schema)
    sheet_name = (data.get("sheet") or "letter").lower()
    if sheet_name not in SHEETS:
        raise UsageError("sheet must be 'letter' or 'a4' (37 CFR 1.84(f))")
    case_default = (data.get("text_case") or "upper").lower()
    validate_keys(data, findings)
    specs = data.get("figures") or []
    if not specs:
        raise UsageError("figures.json lists no figures")
    os.makedirs(out_dir, exist_ok=True)
    base_dir = os.path.dirname(os.path.abspath(figures_path))
    single = len(specs) == 1
    ents = []
    seen_ids = set()
    for f in specs:
        if "id" not in f:
            raise UsageError("every figure needs an 'id' like \"FIG. 1\"")
        if f["id"] in seen_ids:
            raise UsageError("duplicate figure id %s" % f["id"])
        seen_ids.add(f["id"])
        typ = (f.get("type") or "").lower()
        case = (f.get("text_case") or case_default).lower()
        if typ == "image":
            fig = layout_image(f, case, base_dir, out_dir, findings)
        elif typ in LAYOUTS:
            fig = LAYOUTS[typ](f, case)
        else:
            raise UsageError("%s: unknown figure type %r (flowchart, block, sequence, wireframe, graph, image)"
                             % (f["id"], typ))
        # FIG. label below the view, larger than numerals; omitted for a single view, 1.84(u)(1)
        def add_label(fg):
            b = fg.bbox()
            if not single:
                fg.text((b[0] + b[2]) / 2.0, b[3] + 22.0 + FIG_SIZE * CAP_RATIO, fig_label(f["id"]), FIG_SIZE,
                        anchor="middle", bold=True, kind="fig")
        add_label(fig)
        if not fits(fig, sheet_name) and typ in ("flowchart", "sequence"):
            fig2 = LAYOUTS[typ](dict(f, _compact=True), case)
            add_label(fig2)
            fig = fig2
        if not fits(fig, sheet_name) and typ == "block":
            # F32: try the other direction; if neither fits, keep the one drawn at the larger scale
            asked_lr = (f.get("direction") or "TB").upper() in ("LR", "RL", "H", "HORIZONTAL")
            names = ("left-to-right", "top-to-bottom") if asked_lr else ("top-to-bottom", "left-to-right")
            fig2 = layout_block(dict(f, direction="TB" if asked_lr else "LR"), case)
            add_label(fig2)
            s1, s2 = fit_scale(fig, sheet_name), fit_scale(fig2, sheet_name)
            if fits(fig2, sheet_name):
                findings.append({"level": "INFO", "code": "direction-changed", "where": f["id"],
                                 "message": "%s layout does not fit a portrait sheet at 0.32 cm text (scale %.2f); "
                                            "drawn %s (scale %.2f)" % (names[0], s1, names[1], s2)})
                fig = fig2
            else:
                keep2 = s2 > s1 + 1e-6
                findings.append({"level": "INFO", "code": "direction-kept", "where": f["id"],
                                 "message": "neither %s (scale %.2f) nor %s (scale %.2f) fits at 0.32 cm text; kept "
                                            "%s, the larger scale. Split the figure into partial views."
                                            % (names[0], s1, names[1], s2, names[1] if keep2 else names[0])})
                if keep2:
                    fig = fig2
        check_lead_crossings(fig)
        for w in fig.warnings:
            findings.append({"level": "WARN", "code": "lead-lines-cross", "where": f["id"], "message": w})
        for lvl, code, msg in edge_crossings(fig.nodes, fig.edges, fig.numerals):
            findings.append({"level": lvl, "code": code, "where": f["id"], "message": msg})
        ents.append({"id": f["id"], "spec": f, "fig": fig, "type": typ})
    # off-page connectors come in pairs: the letter that ends one view starts the next (F34)
    conn = {}
    for f in specs:
        if (f.get("type") or "").lower() == "flowchart":
            for st in f.get("steps") or []:
                if str(st.get("kind") or "").lower() in ("connector", "off-page", "offpage", "off_page"):
                    conn.setdefault(str(st.get("label", "")).strip().upper(), []).append(f["id"])
    for lab, where in sorted(conn.items()):
        if not lab:
            findings.append({"level": "WARN", "code": "connector-label", "where": where[0],
                             "message": "a connector step needs a letter label, e.g. \"label\": \"A\""})
        elif len(where) < 2:
            findings.append({"level": "WARN", "code": "connector-unpaired", "where": where[0],
                             "message": "connector %s appears only once; add the matching connector %s where the "
                                        "flow continues (next partial view)" % (lab, lab)})
    budgets = [size_budget(e, sheet_name) for e in ents]
    # svg per figure (figure-local coordinates)
    svgs = []
    for e in ents:
        p = os.path.join(out_dir, "%s.svg" % safe_name(e["id"]))
        render_svg(p, e["fig"])
        svgs.append(p)
    placed, geom = pack(ents, sheet_name, findings)
    W, H, sg = geom
    pdf_path = os.path.join(out_dir, "drawings.pdf")
    if _reportlab():
        render_pdf(pdf_path, placed, geom, findings)
    else:
        pdf_path = None
        findings.append({"level": "BLOCK", "code": "no-reportlab", "where": "drawings.pdf",
                         "message": "reportlab not installed (pip install reportlab); SVGs written, PDF not built"})
    # cross-figure numeral consistency, 1.84(p)(4)
    seen = {}
    for e in ents:
        for nm in e["fig"].numerals:
            lab = " ".join(str(nm["label"]).lower().split())
            k = nm["numeral"]
            if k in seen and seen[k][1] != lab:
                findings.append({"level": "BLOCK", "code": "numeral-reused", "where": e["id"],
                                 "message": "numeral %s labels %r here but %r in %s (1.84(p)(4))"
                                            % (k, nm["label"], seen[k][2], seen[k][0])})
            elif k not in seen:
                seen[k] = (e["id"], lab, nm["label"])
    # manifest
    sheets_out = []
    figs_out = []
    for si, row in enumerate(placed):
        sheets_out.append({"number": si + 1, "of": len(placed), "figures": [e["id"] for (e, _, _, _) in row]})
        for (e, ox, oy, s) in row:
            fig = e["fig"]
            nums = []
            for nm in fig.numerals:
                bb = nm["text_bbox"]
                nums.append({"numeral": nm["numeral"], "label": nm["label"],
                             "text_bbox_pt": [round(ox + bb[0] * s, 2), round(oy + bb[1] * s, 2),
                                              round(ox + bb[2] * s, 2), round(oy + bb[3] * s, 2)],
                             "target_pt": [round(ox + nm["target"][0] * s, 2), round(oy + nm["target"][1] * s, 2)]})
            mt = fig.min_text() * s

            def T(pt, ox=ox, oy=oy, s=s):
                return [round(ox + pt[0] * s, 2), round(oy + pt[1] * s, 2)]

            def TB(bb, ox=ox, oy=oy, s=s):
                return [round(ox + bb[0] * s, 2), round(oy + bb[1] * s, 2), round(ox + bb[2] * s, 2),
                        round(oy + bb[3] * s, 2)]
            nodes_out = [{"id": nd["id"], "label": nd.get("label", ""), "numeral": nd.get("numeral"),
                          "parent": nd.get("parent"), "container": nd.get("container", False),
                          "box_pt": TB(nd["box"])} for nd in fig.nodes]
            edges_out = [{"from": ed["from"], "to": ed["to"], "label": ed.get("label", ""),
                          "pts_pt": [T(p_) for p_ in ed["pts"]]} for ed in fig.edges]
            labels_out = [{"edge": el["edge"], "text": el["text"], "box_pt": TB(el["box"])} for el in fig.edge_labels]
            figs_out.append({
                "id": e["id"], "type": e["type"], "title": e["spec"].get("title", ""), "sheet": si + 1,
                "scale": round(s, 4),
                "bbox_pt": [round(v, 2) for v in e["page_bbox"]],
                "bbox_cm": [round(v / PT_PER_CM, 3) for v in e["page_bbox"]],
                "numerals": nums,
                "nodes": nodes_out,
                "edges": edges_out,
                "edge_labels": labels_out,
                "min_text_pt": round(mt, 2),
                "min_cap_height_cm": round(mt * CAP_RATIO / PT_PER_CM, 4),
                "fig_label": None if single else fig_label(e["id"]),
                "warnings": fig.warnings,
            })
    manifest = {
        "schema": SCHEMA_MANIFEST,
        "generated": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "figures_file": os.path.abspath(figures_path),
        "figures_sha256": _sha256(figures_path),
        "sheet": {"name": sheet_name, "width_pt": W, "height_pt": H, "margins_cm": MARGINS_CM,
                  "sight_pt": [round(v, 2) for v in sg], "origin": "top-left, y down, points"},
        "font": {"name": "Bitstream Vera Sans (reportlab Vera.ttf)", "embedded": True,
                 "cap_height_ratio": CAP_RATIO, "min_size_pt": TEXT_MIN},
        "text_case": case_default,
        "single_view": single,
        "sheets": sheets_out,
        "figures": figs_out,
        "budget": budgets,
        "svgs": [os.path.basename(p) for p in svgs],
        "pdf": os.path.basename(pdf_path) if pdf_path else None,
        "findings": findings,
    }
    man_path = os.path.join(out_dir, "drawings-manifest.json")
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    if pdf_path:
        _audit(d, {"kind": "export", "path": os.path.relpath(pdf_path, d) if d else pdf_path,
                   "sha256": _sha256(pdf_path), "script": "drawings.py"}, no_audit)
    blocking = sum(1 for f in findings if f["level"] == "BLOCK")
    return {"ok": blocking == 0, "pdf": pdf_path, "svgs": svgs, "manifest": man_path,
            "sheets": len(placed), "figures": len(ents), "findings": findings, "budget": budgets,
            "summary": {"blocking": blocking, "warnings": sum(1 for f in findings if f["level"] == "WARN")}}


def run(args: dict) -> dict:
    """Tool entry point. args: {command:'build', figures, out, dir?, no_audit?}"""
    cmd = args.get("command", "build")
    if cmd != "build":
        raise UsageError("unknown command %r" % cmd)
    d = args.get("dir", "patent")
    figs = _resolve(args["figures"], d)
    out = args.get("out") or os.path.join(os.path.dirname(figs), "out")
    if not os.path.isabs(out) and not os.path.exists(os.path.dirname(out.rstrip("/")) or "."):
        out = os.path.join(d, out)
    if not os.path.exists(figs):
        raise UsageError("figures file not found: %s" % args["figures"])
    return build(figs, out, d=d, no_audit=bool(args.get("no_audit")))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build 37 CFR 1.84 drawing sheets (PDF) and SVGs from figures.json")
    sub = ap.add_subparsers(dest="command")
    b = sub.add_parser("build", help="figures.json -> SVG per figure + drawings.pdf + manifest")
    b.add_argument("figures")
    b.add_argument("--out", default=None)
    for p in (ap, b):
        p.add_argument("--dir", default="patent")
        p.add_argument("--json", action="store_true")
        p.add_argument("--no-audit", action="store_true")
    a = ap.parse_args(argv)
    if a.command != "build":
        ap.print_help()
        return 2
    try:
        res = run({"command": "build", "figures": a.figures, "out": a.out, "dir": a.dir, "no_audit": a.no_audit})
    except UsageError as ex:
        if a.json:
            print(json.dumps({"error": str(ex)}))
        else:
            print("error: %s" % ex, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print("%s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
        print("size budget (0.32 cm text, %s sheet):" % "portrait")
        for b in res.get("budget", []):
            print("  " + b["message"])
        print("built %d figure(s) on %d sheet(s): %s" % (res["figures"], res["sheets"], res["pdf"]))
        print("svg: %s" % ", ".join(os.path.basename(p) for p in res["svgs"]))
        print("manifest: %s" % res["manifest"])
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
