#!/usr/bin/env python3
"""Column:line pinpoints for issued US patents, read from the printed grant PDF.

Issued US patents (B1/B2, older kind A, reissues) print column numbers and gutter line numbers,
not paragraph numbers. Our cache only holds Google's HTML text, so grant pinpoints from
quote_check.py are synthetic (p1..pN). This script downloads the grant PDF and maps a quote to
"col. 4, ll. 10-22" using the PDF's OCR text layer and the printed numbers.

Examples:
    python3 scripts/colline.py fetch US9457709B2              # -> <dir>/cache/pdf/US9457709B2.pdf
    python3 scripts/colline.py fetch US5560126A --file "Patent 5560126.pdf"   # import a local copy
    python3 scripts/colline.py locate US9457709B2 "turn signals attached to the head protection enclosure"
    python3 scripts/colline.py layout US9457709B2             # show detected spec pages / columns
    python3 scripts/colline.py annotate --from patent/prior-art.json
    python3 scripts/colline.py annotate --chart charts/r1.json --dry-run --json

How locate works:
  1. Specification pages are the pages with two columns of body text and a vertical run of gutter
     line numbers (5, 10, 15, ...). The front page and drawing sheets have neither and are skipped.
  2. Each page's gutter numbers give a line grid (lines are evenly spaced): y = y1 + (line-1)*pitch,
     fitted with outlier rejection, so misread or missing numbers do not matter. Pages with few
     numbers take the document's pitch.
  3. Words are grouped into printed text lines per column. Line numbers are positional: a text line
     takes the number of the nearest grid position. Where a text line sits midway between two
     positions (half-line paragraph gaps in older patents, or text drifting against the gutter
     numbers), the cited range widens by one line at that end so it always covers the quote
     ("note: range widened" in reasons).
  4. Column numbers are the small numerals centred above each column. They are cross-checked
     against the page sequence (spec page k holds columns 2k+1 and 2k+2).
  5. The quote and the page text are reduced to lower-case letters and digits, which forgives
     line-end hyphenation, ligatures, quote marks, dashes, and OCR word splits. An exact match is
     tried first, then a fuzzy match (seeded n-grams + difflib) that tolerates OCR errors. When the
     same words occur twice (spec and claims), the first wins unless --context picks another; the
     rest are listed under "also".
  6. A quote that runs across a column or page break gives "col. 4, l. 60 – col. 5, l. 3".

Confidence:
  high  match score >= 0.92; the start and end pages each have >= 3 gutter numbers on one grid;
        column numbers are confirmed by the printed numerals (or the page sequence they support).
  low   anything weaker (fuzzy OCR match, grid borrowed from another page, unconfirmed column
        numbers, margin line numbers). Check the PDF before citing a low result.
  none  not found: no text layer (image-only PDF; this script does not OCR), no column/line layout,
        or no passage scoring >= 0.80. It never guesses.

annotate fills `pinpoint_colline` on prior-art element_map entries and chart cells that cite a US
grant, carry a quote, and have a synthetic pinpoint (pN or empty). The original `pinpoint` field is
never changed. Only high-confidence results are written to `pinpoint_colline`; a low result goes
to `pinpoint_colline_candidate` with a WARN so a person checks it.

Network: only `fetch` (and `locate`/`annotate` when a PDF is missing and --offline is not given)
touch the network: Google Patents (through patent_fetch.py) for the PDF link, then
patentimages.storage.googleapis.com for the PDF. Generic User-Agent, >=1 s spacing per host,
2 retries with backoff, everything cached under <dir>/cache/.

Requires PyMuPDF (`pip3 install pymupdf`, imported as fitz).
Exit codes: 0 ok, 1 not found / not located, 2 bad input, 3 network or source failure.
"""

import argparse
import bisect
import collections
import difflib
import glob
import gzip
import json
import os
import re
import shutil
import sys
import unicodedata
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from normalize_number import fetch_candidates, kindless, normalize  # noqa: E402
from state import (SCHEMA_CHART, SCHEMA_PRIOR_ART, SourceError, UsageError, add_common, audit,  # noqa: E402
                   check_schema, cli_main, finalize, finding, new_result, read_json, to_namespace,
                   write_json)

GRANT_TYPES = ("patent", "reissue", "plant", "design")
PDF_HOSTS = ("patentimages.storage.googleapis.com",)
HIGH_SCORE = 0.92      # fuzzy score needed for a high-confidence pinpoint
MIN_SCORE = 0.80       # below this the quote is "not found"
MIN_QUOTE_CHARS = 12   # letters+digits; shorter quotes cannot be placed reliably
AMBIG_FRAC = 0.35      # a word this far (in line pitches) from a grid line is ambiguous
RANGE_DASH = "-"       # within one column: "ll. 10-22"
SPAN_DASH = " – "      # across columns: "col. 4, l. 60 – col. 5, l. 3"
SYNTHETIC_PIN = re.compile(r"^p\d+$")


def _fitz():
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise UsageError("PyMuPDF is required for colline.py: pip3 install pymupdf")
    return fitz


# --------------------------------------------------------------------------- page layout


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def _clusters(points, tol):
    """Group (xc, yc, value) points whose x-centres lie within tol of the running group."""
    out = []
    for p in sorted(points):
        if out and p[0] - out[-1][-1][0] <= tol:
            out[-1].append(p)
        else:
            out.append([p])
    return out


def _fit_grid(points, height):
    """Robust line grid from gutter numbers: y = y1 + (value-1)*pitch. Returns dict or None."""
    pmin, pmax = height / 130.0, height / 40.0
    best = None
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            (_, yi, vi), (_, yj, vj) = points[i], points[j]
            if vi == vj:
                continue
            pitch = (yj - yi) / float(vj - vi)
            if not pmin <= pitch <= pmax:
                continue
            y1 = yi - (vi - 1) * pitch
            inl = {}
            for p in points:
                r = abs(p[1] - (y1 + (p[2] - 1) * pitch))
                if r < 0.3 * pitch and (p[2] not in inl or r < inl[p[2]][0]):
                    inl[p[2]] = (r, p)
            if best is None or len(inl) > len(best):
                best = inl
    if not best or len(best) < 2:
        return None
    pts = [v[1] for v in best.values()]
    n = len(pts)
    mv = sum(p[2] for p in pts) / float(n)
    my = sum(p[1] for p in pts) / float(n)
    sxx = sum((p[2] - mv) ** 2 for p in pts)
    pitch = sum((p[2] - mv) * (p[1] - my) for p in pts) / sxx
    y1 = my - (mv - 1) * pitch
    rms = (sum((p[1] - (y1 + (p[2] - 1) * pitch)) ** 2 for p in pts) / n) ** 0.5
    return {"xc": _median([p[0] for p in pts]), "y1": y1, "pitch": pitch, "n": n,
            "rms": rms, "values": sorted(p[2] for p in pts), "points": sorted((p[2], p[1]) for p in pts)}


def _refit(grid, pitch):
    """Same grid with a fixed pitch: y1 = median of the markers' implied line-1 positions.

    Spec pages of one patent share one layout, so a page with few gutter numbers (or one
    misread box) takes the document pitch instead of its own noisy estimate."""
    y1 = _median([y - (v - 1) * pitch for v, y in grid["points"]])
    rms = (sum((y - (y1 + (v - 1) * pitch)) ** 2 for v, y in grid["points"]) / len(grid["points"])) ** 0.5
    g = dict(grid)
    g.update({"y1": y1, "pitch": pitch, "rms": rms})
    return g


def _gutter_candidates(words, width, height):
    out = []
    for w in words:
        t = w[4]
        if t.isdigit() and len(t) <= 2:
            v = int(t)
            if v % 5 == 0 and 5 <= v <= 95 and (w[2] - w[0]) < 0.05 * width and (w[3] - w[1]) < 0.05 * height:
                out.append(((w[0] + w[2]) / 2.0, (w[1] + w[3]) / 2.0, v))
    return out


def _gap_split(words, width):
    """x of the widest empty vertical band in the middle of the page, else None (margin layouts)."""
    lo, hi = int(width * 0.3), int(width * 0.7)
    cover = [0] * (hi - lo + 1)
    for w in words:
        a, b = max(lo, int(w[0])), min(hi, int(w[2]) + 1)
        for x in range(a, b):
            cover[x - lo] += 1
    best, run, start = None, 0, None
    for i, c in enumerate(cover + [99]):
        if c == 0:
            if run == 0:
                start = i
            run += 1
        else:
            if run and (best is None or run > best[0]):
                best = (run, start)
            run = 0
    if not best or best[0] < 4:
        return None
    return lo + best[1] + best[0] / 2.0


_HEAD_MAP = str.maketrans({"l": "1", "I": "1", "|": "1", "O": "0", "o": "0"})


def _header_number(text):
    t = text.strip(".,:;'`\"").translate(_HEAD_MAP)
    if t.isdigit() and 1 <= len(t) <= 3 and int(t) > 0:
        return int(t)
    return None


def _assign(page, grid, split, gutter_x, tol):
    """Body words of one page -> (left, right) lists with fractional line numbers."""
    y1, pitch = grid["y1"], grid["pitch"]
    max_line = (page["height"] - y1) / pitch + 1.5
    left, right, straddle = [], [], 0
    for w in page["words"]:
        xc, yc = (w[0] + w[2]) / 2.0, (w[1] + w[3]) / 2.0
        if gutter_x is not None and w[4].isdigit() and abs(xc - gutter_x) <= tol:
            continue  # gutter line number (or a misread one)
        lf = (yc - y1) / pitch + 1
        if lf < 0.5 or lf > max_line:
            continue
        if w[0] < split - 2 and w[2] > split + 2:
            straddle += 1
        rec = {"x0": w[0], "x1": w[2], "yc": yc, "lf": lf, "text": w[4]}
        (left if xc < split else right).append(rec)
    return left, right, straddle


def _read_col_numbers(page, grid, left, right):
    """Printed column numerals centred above each column: [left_value|None, right_value|None]."""
    y1, pitch = grid["y1"], grid["pitch"]
    out = []
    for side in (left, right):
        if len(side) < 3:
            out.append(None)
            continue
        x0s = sorted(r["x0"] for r in side)
        x1s = sorted(r["x1"] for r in side)
        c0, c1 = x0s[len(x0s) // 20], x1s[-1 - len(x1s) // 20]
        centre, half = (c0 + c1) / 2.0, (c1 - c0) / 2.0
        best = None
        for w in page["words"]:
            xc, yc = (w[0] + w[2]) / 2.0, (w[1] + w[3]) / 2.0
            if not (y1 - 4.5 * pitch <= yc <= y1 - 0.5 * pitch):
                continue
            if abs(xc - centre) > 0.3 * (2 * half):
                continue
            v = _header_number(w[4])
            if v is not None and (best is None or abs(xc - centre) < best[0]):
                best = (abs(xc - centre), v)
        out.append(best[1] if best else None)
    return out


def _text_lines(side, pitch):
    """Group a column's words into printed text lines and give each a grid line number.

    Lines are positional: a text line takes the number of the nearest gutter grid position.
    Older patents add half-line gaps between paragraphs, so a text line can sit midway between
    two positions; it is flagged `amb` and a pinpoint then widens by one line to cover both."""
    groups = []
    for r in sorted(side, key=lambda r: r["yc"]):
        if groups and r["yc"] - groups[-1]["ym"] <= 0.6 * pitch:
            g = groups[-1]
            g["words"].append(r)
            g["ym"] = sum(w["yc"] for w in g["words"]) / len(g["words"])
            g["lfs"].append(r["lf"])
        else:
            groups.append({"words": [r], "ym": r["yc"], "lfs": [r["lf"]]})
    out = []
    for g in groups:
        lf = _median(g["lfs"])
        line = int(lf + 0.5)
        out.append({"words": g["words"], "lf": lf, "line": max(1, line), "amb": abs(lf - line) > AMBIG_FRAC})
    return out


def analyze_pdf(path):
    """Read a grant PDF into a layout: spec pages, line grids, column numbers, word stream."""
    fitz = _fitz()
    doc = fitz.open(path)
    pages = []
    total_words = 0
    for i, pg in enumerate(doc):
        words = [w for w in pg.get_text("words") if w[4].strip()]
        total_words += len(words)
        pages.append({"index": i, "page": i + 1, "width": pg.rect.width, "height": pg.rect.height,
                      "words": words, "kind": "other"})
    doc.close()
    lay = {"pdf": path, "page_count": len(pages), "total_words": total_words, "spec_pages": [],
           "problems": [], "stream": [], "D": "", "starts": [], "_grams": {}}
    if total_words < 50 * max(1, len(pages) // 10):
        lay["problems"].append("no text layer (image-only PDF); colline.py does not OCR")
        return lay

    # pass 1: pages with their own gutter grid
    for pg in pages:
        W, H = pg["width"], pg["height"]
        if len(pg["words"]) < 30:
            pg["kind"] = "sparse"
            continue
        tol = 8.0 * W / 612.0
        best = None
        for cl in _clusters(_gutter_candidates(pg["words"], W, H), tol):
            g = _fit_grid(cl, H)
            if g is None:
                continue
            g["middle"] = 0.35 * W <= g["xc"] <= 0.65 * W
            if best is None or (g["n"], g["middle"]) > (best["n"], best["middle"]):
                best = g
        if best is None:
            continue
        if best["middle"]:
            layout, split, gx = "gutter", best["xc"], best["xc"]
        else:
            split = _gap_split(pg["words"], W)
            layout, gx = "margin", best["xc"]
            if split is None:
                continue
        left, right, straddle = _assign(pg, best, split, gx, tol)
        if len(left) < 20 or straddle > 0.05 * (len(left) + len(right)):
            continue
        pg.update({"kind": "spec", "grid": best, "grid_source": "markers", "layout": layout,
                   "split": split, "gutter_x": gx, "tol": tol, "left": left, "right": right})

    spec = [p for p in pages if p["kind"] == "spec"]
    if not spec:
        lay["problems"].append("no specification pages with two text columns and gutter line numbers")
        return lay

    # document pitch from well-marked pages; pages with few markers (or an off pitch) take it
    rich = [p["grid"]["pitch"] for p in spec if p["grid"]["n"] >= 6] or [p["grid"]["pitch"] for p in spec]
    doc_pitch = _median(rich)
    for pg in spec:
        g = pg["grid"]
        if g["n"] < 6 or abs(g["pitch"] - doc_pitch) > 0.01 * doc_pitch:
            pg["grid"] = _refit(g, doc_pitch)
            pg["left"], pg["right"], _ = _assign(pg, pg["grid"], pg["split"], pg["gutter_x"], pg["tol"])

    # pass 2: neighbouring pages (e.g. a short last page) borrow the grid of the others
    med = {"pitch": doc_pitch, "y1": _median([p["grid"]["y1"] for p in spec]),
           "split": _median([p["split"] for p in spec]), "gx": _median([p["gutter_x"] for p in spec])}
    layout0 = spec[0]["layout"]
    changed = True
    while changed:
        changed = False
        idxs = [p["index"] for p in pages if p["kind"] == "spec"]
        for cand in (min(idxs) - 1, max(idxs) + 1):
            if not 0 <= cand < len(pages):
                continue
            pg = pages[cand]
            if pg["kind"] == "spec" or len(pg["words"]) < 20 or pg.get("_tried"):
                continue
            pg["_tried"] = True
            tol = 8.0 * pg["width"] / 612.0
            near = [c for c in _gutter_candidates(pg["words"], pg["width"], pg["height"])
                    if abs(c[0] - med["gx"]) <= tol]
            grid = {"pitch": med["pitch"], "y1": med["y1"], "n": 0, "rms": None, "values": [], "xc": med["gx"]}
            source = "borrowed"
            if near:
                ys = [c[1] - (c[2] - 1) * med["pitch"] for c in near]
                y1 = _median(ys)
                if abs(y1 - med["y1"]) < 3 * med["pitch"]:
                    grid.update({"y1": y1, "n": len(near), "values": sorted(c[2] for c in near)})
                    source = "one_marker" if len(near) == 1 else "markers_borrowed_pitch"
            left, right, straddle = _assign(pg, grid, med["split"], med["gx"], tol)
            if len(left) < 5 or straddle > 0.05 * (len(left) + len(right)):
                continue
            pg.update({"kind": "spec", "grid": grid, "grid_source": source, "layout": layout0,
                       "split": med["split"], "gutter_x": med["gx"], "tol": tol, "left": left, "right": right,
                       "needs_header": True})
            changed = True

    spec = sorted([p for p in pages if p["kind"] == "spec"], key=lambda p: p["index"])

    # column numbers: printed numerals, checked against the page sequence
    offsets = collections.Counter()
    for k, pg in enumerate(spec):
        pg["read"] = _read_col_numbers(pg, pg["grid"], pg["left"], pg["right"])
        for s, v in enumerate(pg["read"]):
            if v is not None:
                offsets[v - (2 * k + 1 + s)] += 1
    if offsets:
        off, support = offsets.most_common(1)[0]
    else:
        off, support = 0, 0
    keep = []
    for k, pg in enumerate(spec):
        exp = [2 * k + 1 + off, 2 * k + 2 + off]
        rl, rr = pg["read"]
        own = None
        if rl is not None and rr is not None and rr == rl + 1:
            own = [rl, rr]
        elif rl is not None and rr is None:
            own = [rl, rl + 1]
        elif rr is not None and rl is None:
            own = [rr - 1, rr]
        if own == exp:
            pg["cols"], pg["cols_source"] = exp, "printed"
        elif own is not None and rl is not None and rr is not None:
            pg["cols"], pg["cols_source"] = own, "printed_conflicts_sequence"
        else:
            pg["cols"], pg["cols_source"] = exp, "sequence"
        if pg.get("needs_header") and pg["cols_source"] != "printed":
            pg["kind"] = "other"  # a borrowed-grid page must prove itself with printed column numbers
            continue
        keep.append(pg)
    spec = keep
    lay["col_offset_support"] = support
    lay["layout"] = layout0

    # word stream in reading order: text lines per column, each mapped to the gutter grid
    stream, parts, starts, pos = [], [], [], 0
    for pg in spec:
        pg["ambiguous_lines"] = [0, 0]
        for s, side in enumerate((pg["left"], pg["right"])):
            for tl in _text_lines(side, pg["grid"]["pitch"]):
                if tl["amb"]:
                    pg["ambiguous_lines"][s] += 1
                for r in sorted(tl["words"], key=lambda r: r["x0"]):
                    n = _norm_chars(r["text"])
                    stream.append({"page": pg["page"], "col": pg["cols"][s], "line": tl["line"],
                                   "lf": round(tl["lf"], 3), "amb": tl["amb"], "text": r["text"]})
                    starts.append(pos)
                    parts.append(n)
                    pos += len(n)
    lay["stream"], lay["starts"], lay["D"] = stream, starts, "".join(parts)
    lay["spec_pages"] = [{
        "page": p["page"], "columns": p["cols"], "columns_source": p["cols_source"],
        "printed_numerals": p["read"], "grid_source": p["grid_source"], "markers": p["grid"]["n"],
        "marker_values": p["grid"]["values"], "pitch": round(p["grid"]["pitch"], 3),
        "line1_y": round(p["grid"]["y1"], 2), "rms": (round(p["grid"]["rms"], 3) if p["grid"]["rms"] is not None
                                                      else None),
        "layout": p["layout"], "split_x": round(p["split"], 1), "ambiguous_lines": p["ambiguous_lines"],
        "words": [len(p["left"]), len(p["right"])]} for p in spec]
    lay["_pages"] = {p["page"]: p for p in spec}
    return lay


_LAYOUTS = {}


def get_layout(path):
    key = (os.path.abspath(path), os.path.getmtime(path), os.path.getsize(path))
    if key not in _LAYOUTS:
        _LAYOUTS[key] = analyze_pdf(path)
    return _LAYOUTS[key]


# --------------------------------------------------------------------------- matching


def _norm_chars(s):
    """Lower-case ASCII letters and digits only (ligatures and accents folded)."""
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(ch for ch in s.lower() if ch.isascii() and ch.isalnum())


ELLIPSIS_RE = re.compile(r"\s*(?:\.\s*\.\s*\.|…)\s*")


def _grams(lay, k):
    g = lay["_grams"].get(k)
    if g is None:
        g = collections.defaultdict(list)
        D = lay["D"]
        for i in range(len(D) - k + 1):
            g[D[i:i + k]].append(i)
        lay["_grams"][k] = g
    return g


def _align(Q, D, w0, w1):
    """Fuzzy-align Q inside D[w0:w1] -> (score, start, end) in D coordinates."""
    sm = difflib.SequenceMatcher(None, Q, D[w0:w1], autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 3]
    if not blocks:
        return 0.0, None, None
    tol = max(8, int(0.08 * len(Q)))
    diags = [b.b - b.a for b in blocks]
    best_d = max(diags, key=lambda d: sum(b.size for b in blocks if abs((b.b - b.a) - d) <= tol))
    kept = sorted([b for b in blocks if abs((b.b - b.a) - best_d) <= tol], key=lambda b: b.a)
    matched = sum(b.size for b in kept)
    s = w0 + kept[0].b - kept[0].a
    last = kept[-1]
    e = w0 + last.b + last.size + (len(Q) - last.a - last.size)
    s, e = max(0, s), min(len(D), e)
    return matched / float(len(Q)), s, e


def _candidates(Q, lay, lo=0, hi=None):
    """[(score, start, end)] best first, searching D[lo:hi]."""
    D = lay["D"]
    hi = len(D) if hi is None else min(hi, len(D))
    out = []
    i = D.find(Q, lo, hi)
    while i >= 0 and len(out) < 25:
        out.append((1.0, i, i + len(Q)))
        i = D.find(Q, i + 1, hi)
    if out:
        return out
    k = 8 if len(Q) >= 40 else max(5, len(Q) // 4)
    grams = _grams(lay, k)
    votes = collections.Counter()
    for qi in range(len(Q) - k + 1):
        hits = grams.get(Q[qi:qi + k])
        if not hits or len(hits) > 50:
            continue
        for dp in hits:
            if lo <= dp < hi:
                votes[(dp - qi) // 16] += 1
    if not votes:
        return []
    bins = sorted(votes, key=lambda b: -(votes[b] + votes.get(b - 1, 0) + votes.get(b + 1, 0)))
    chosen = []
    for b in bins:
        if all(abs(b - c) * 16 > max(32, len(Q) // 2) for c in chosen):
            chosen.append(b)
        if len(chosen) >= 4:
            break
    slack = max(30, len(Q) // 5)
    for b in chosen:
        diag = b * 16
        w0, w1 = max(lo, diag - slack), min(hi, diag + len(Q) + slack + 16)
        if w1 <= w0:
            continue
        sc, s, e = _align(Q, D, w0, w1)
        if s is not None:
            out.append((sc, s, e))
    out.sort(key=lambda x: -x[0])
    return out


def _owner(lay, c):
    return max(0, bisect.bisect_right(lay["starts"], c) - 1)


def _pick_by_context(cands, Q, context, lay):
    """Among near-equal candidates, prefer the one whose surroundings match the context paragraph."""
    C = _norm_chars(context)
    if len(C) <= len(Q) + 4:
        return cands[0]
    cq = C.find(Q)
    if cq < 0:
        cq = 0
    D = lay["D"]
    sm = difflib.SequenceMatcher(autojunk=False)
    best = None
    for cand in cands:
        s = cand[1]
        a, b = max(0, s - cq), min(len(D), s - cq + len(C))
        sm.set_seqs(C, D[a:b])
        r = sm.quick_ratio()
        if r >= 0.5:
            r = sm.ratio()
        if best is None or r > best[0]:
            best = (r, cand)
    return best[1]


def _joined_text(lay, i0, i1):
    out = []
    for i in range(i0, i1 + 1):
        w = lay["stream"][i]
        t = w["text"]
        if out and out[-1].endswith("-") and lay["stream"][i - 1]["line"] != w["line"]:
            out[-1] = out[-1][:-1] + t
        else:
            out.append(t)
    return " ".join(out)


def _span(lay, i0, i1):
    """Start/end positions for stream words i0..i1. A start or end text line that sits between
    two grid positions widens the range by one line so the cited lines always cover the quote."""
    a, b = dict(lay["stream"][i0]), dict(lay["stream"][i1])
    widened = False
    if a["amb"]:
        lo = max(1, min(a["line"], int(a["lf"])))
        widened = widened or lo != a["line"]
        a["line"] = lo
    if b["amb"]:
        hi = max(b["line"], int(b["lf"]) + 1)
        widened = widened or hi != b["line"]
        b["line"] = hi
    return a, b, widened


def format_pinpoint(a, b):
    if a["col"] == b["col"]:
        if a["line"] == b["line"]:
            return "col. %d, l. %d" % (a["col"], a["line"])
        return "col. %d, ll. %d%s%d" % (a["col"], a["line"], RANGE_DASH, b["line"])
    return "col. %d, l. %d%scol. %d, l. %d" % (a["col"], a["line"], SPAN_DASH, b["col"], b["line"])


def _not_found(reason, **extra):
    out = {"found": False, "pinpoint": None, "page": None, "confidence": None, "matched_text": None,
           "reason": reason}
    out.update(extra)
    return out


def locate(pdf_path, quote, context=None):
    """Map a quote to a column:line pinpoint in a grant PDF. Pure (no network, no writes).

    Returns {"found", "pinpoint", "page", "confidence": "high"|"low"|None, "matched_text",
             "score", "start", "end", "end_page", "also", "reasons", "reason"}."""
    lay = get_layout(pdf_path)
    if lay["problems"]:
        return _not_found("; ".join(lay["problems"]))
    parts = [p for p in ELLIPSIS_RE.split(quote or "") if _norm_chars(p)]
    if not parts:
        return _not_found("empty quote")
    Qs = [_norm_chars(p) for p in parts]
    if sum(len(q) for q in Qs) < MIN_QUOTE_CHARS:
        return _not_found("quote too short to place reliably (%d letters/digits)" % sum(len(q) for q in Qs))
    first = _candidates(Qs[0], lay)
    if not first or first[0][0] < MIN_SCORE:
        best = first[0] if first else None
        extra = {}
        if best and best[1] is not None:
            i0, i1 = _owner(lay, best[1]), _owner(lay, max(best[1], best[2] - 1))
            pa, pb, _ = _span(lay, i0, i1)
            extra = {"closest": {"score": round(best[0], 3), "pinpoint": format_pinpoint(pa, pb),
                                 "text": _joined_text(lay, i0, i1)}}
        return _not_found("no passage matches the quote (best score %.2f < %.2f)"
                          % (best[0] if best else 0.0, MIN_SCORE), **extra)
    top = [c for c in first if c[0] >= first[0][0] - 0.02]
    pick = top[0]
    if len(top) > 1 and context:
        pick = _pick_by_context(top, Qs[0], context, lay)
    score_parts, start, end = [pick[0]], pick[1], pick[2]
    for q in Qs[1:]:
        nxt = _candidates(q, lay, end, end + 3000 + 2 * len(q))
        if not nxt or nxt[0][0] < MIN_SCORE:
            return _not_found("ellipsis part not found after the first part: %r" % q[:40])
        score_parts.append(nxt[0][0])
        end = nxt[0][2]
    total = float(sum(len(q) for q in Qs))
    score = sum(s * len(q) for s, q in zip(score_parts, Qs)) / total
    i0, i1 = _owner(lay, start), _owner(lay, max(start, end - 1))
    a, b, widened = _span(lay, i0, i1)
    reasons = []
    if widened:
        reasons.append("note: range widened by one line (text sits between gutter line positions)")
    if score < HIGH_SCORE:
        reasons.append("fuzzy match %.2f < %.2f (OCR differences)" % (score, HIGH_SCORE))
    elif score < 1.0:
        reasons.append("note: fuzzy match %.3f" % score)
    for w in (a, b):
        pg = lay["_pages"][w["page"]]
        if pg["grid_source"] != "markers" or pg["grid"]["n"] < 3:
            reasons.append("page %d line grid from %s (%d gutter numbers)" % (w["page"], pg["grid_source"],
                                                                                pg["grid"]["n"]))
        if pg["cols_source"] != "printed" and lay["col_offset_support"] < 2:
            reasons.append("page %d column numbers not confirmed by printed numerals" % w["page"])
        if pg["cols_source"] == "printed_conflicts_sequence":
            reasons.append("page %d printed column numbers conflict with page sequence" % w["page"])
        if pg["layout"] != "gutter":
            reasons.append("line numbers at the page margin (layout not verified)")
    reasons = list(dict.fromkeys(reasons))
    confidence = "high" if not [r for r in reasons if not r.startswith("note:")] else "low"
    also = []
    for c in first:
        if c is pick or c[0] < max(MIN_SCORE, pick[0] - 0.02):
            continue
        j0, j1 = _owner(lay, c[1]), _owner(lay, max(c[1], c[2] - 1))
        pa, pb, _ = _span(lay, j0, j1)
        pin = format_pinpoint(pa, pb)
        if pin not in also:
            also.append(pin)
    return {"found": True, "pinpoint": format_pinpoint(a, b), "page": a["page"], "end_page": b["page"],
            "confidence": confidence, "score": round(score, 3), "matched_text": _joined_text(lay, i0, i1),
            "start": {"page": a["page"], "column": a["col"], "line": a["line"]},
            "end": {"page": b["page"], "column": b["col"], "line": b["line"]},
            "also": also[:5], "reasons": reasons, "reason": None, "pdf": pdf_path}


# --------------------------------------------------------------------------- cache + fetch


def pdf_dir(dirpath):
    return os.path.join(dirpath, "cache", "pdf")


def _safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)


def _check_grant(number):
    norm = normalize(number)
    if not norm.get("ok"):
        raise UsageError("cannot parse number %r: %s" % (number, "; ".join(norm.get("notes") or [])))
    if norm["country"] != "US" or norm["doc_type"] not in GRANT_TYPES:
        raise UsageError("%s is not an issued US patent; published applications print paragraph numbers "
                         "([0018]) and need no column:line pinpoints" % norm["canonical"])
    return norm


def find_pdf(dirpath, number):
    """Path of a cached grant PDF for `number` (kind-less numbers match any kind), else None."""
    norm = normalize(number)
    if not norm.get("ok"):
        return None
    names = list(fetch_candidates(norm)) + [norm["canonical"]]
    for n in names:
        p = os.path.join(pdf_dir(dirpath), _safe(n) + ".pdf")
        if os.path.exists(p):
            return p
    base = kindless(norm["canonical"])
    for p in sorted(glob.glob(os.path.join(pdf_dir(dirpath), _safe(base) + "*.pdf"))):
        if re.match(r"^%s(?:[A-Z]\d?)?$" % re.escape(base), os.path.basename(p)[:-4]):
            return p
    return None


_PDF_META = re.compile(r"<meta\b[^>]*\bname=[\"']citation_pdf_url[\"'][^>]*>", re.I)
_CONTENT = re.compile(r"\bcontent=[\"']([^\"']+)[\"']", re.I)
_PDF_LINK = re.compile(r"<a\b[^>]*itemprop=[\"']pdfLink[\"'][^>]*\bhref=[\"']([^\"']+)[\"']", re.I)


def pdf_url_from_html(html):
    m = _PDF_META.search(html)
    if m:
        c = _CONTENT.search(m.group(0))
        if c:
            return c.group(1)
    m = _PDF_LINK.search(html)
    return m.group(1) if m else None


def _raw_html(dirpath, number):
    p = os.path.join(dirpath, "cache", "raw", "google_patents", _safe(number + ".html") + ".gz")
    if not os.path.exists(p):
        return None
    with gzip.open(p, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def pdf_url_for(dirpath, number, offline=False, no_audit=False):
    """(pdf_url, canonical_number, how) from the cached record, its raw HTML, or a fresh fetch."""
    import patent_fetch
    _, rec = patent_fetch.find_cached(dirpath, number, any_kind=True)
    if rec is not None and rec.get("country") == "US":
        if rec.get("pdf_url"):
            return rec["pdf_url"], rec.get("number"), "cached record"
        html = _raw_html(dirpath, rec.get("number") or "")
        url = pdf_url_from_html(html) if html else None
        if url:
            return url, rec.get("number"), "cached Google Patents HTML"
    if offline:
        return None, (rec or {}).get("number"), "offline: no PDF link in cache"
    r = patent_fetch.fetch_one(number, dirpath, offline=False, force=rec is not None, no_audit=no_audit,
                               enrich=False)
    if r.get("status") == "network_error":
        raise SourceError(r.get("message") or "Google Patents unreachable")
    rec = r.get("record")
    if not rec:
        return None, None, r.get("message") or r.get("status")
    url = rec.get("pdf_url")
    if not url:
        html = _raw_html(dirpath, rec.get("number") or "")
        url = pdf_url_from_html(html) if html else None
    return url, rec.get("number"), "Google Patents page"


def fetch_pdf(dirpath, number, offline=False, force=False, file=None, no_audit=False):
    """Put the grant PDF for `number` at <dir>/cache/pdf/<NUMBER>.pdf. Returns a status dict."""
    norm = _check_grant(number)
    out = {"input": number, "status": None, "path": None, "url": None, "message": None}
    if not force and not file:
        p = find_pdf(dirpath, number)
        if p:
            out.update({"status": "cached", "path": p})
            return out
    if file:
        if not os.path.exists(file):
            raise UsageError("--file not found: %s" % file)
        with open(file, "rb") as fh:
            if fh.read(5) != b"%PDF-":
                raise UsageError("%s is not a PDF" % file)
        dest = os.path.join(pdf_dir(dirpath), _safe(norm["canonical"]) + ".pdf")
        os.makedirs(pdf_dir(dirpath), exist_ok=True)
        shutil.copyfile(file, dest + ".tmp")
        os.replace(dest + ".tmp", dest)
        audit(dirpath, "fetch", no_audit, number=norm["canonical"], source="local_file", ok=True, doc="pdf")
        out.update({"status": "imported", "path": dest})
        return out
    if offline and not find_pdf(dirpath, number):
        out.update({"status": "not_cached", "message": "offline and no PDF in cache/pdf/"})
        return out
    url, canonical, how = pdf_url_for(dirpath, number, offline=offline, no_audit=no_audit)
    if not url:
        out.update({"status": "not_found", "message": "no PDF link found (%s)" % how})
        return out
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or u.netloc not in PDF_HOSTS:
        out.update({"status": "not_found", "url": url,
                    "message": "PDF link is not on %s; refusing to fetch" % ", ".join(PDF_HOSTS)})
        return out
    from patent_fetch import http_request
    try:
        status, body, _ = http_request(url, headers={"Accept": "application/pdf"}, timeout=60)
    except SourceError as e:
        audit(dirpath, "fetch", no_audit, number=canonical or norm["canonical"], source="patentimages",
              ok=False, error=str(e), doc="pdf")
        out.update({"status": "network_error", "url": url, "message": str(e)})
        return out
    if status != 200 or not body.startswith(b"%PDF-"):
        msg = "HTTP %d" % status if status != 200 else "response is not a PDF"
        audit(dirpath, "fetch", no_audit, number=canonical or norm["canonical"], source="patentimages",
              ok=False, error=msg, doc="pdf")
        out.update({"status": "network_error" if status >= 500 else "not_found", "url": url, "message": msg})
        return out
    name = canonical or norm["canonical"]
    dest = os.path.join(pdf_dir(dirpath), _safe(name) + ".pdf")
    os.makedirs(pdf_dir(dirpath), exist_ok=True)
    with open(dest + ".tmp", "wb") as fh:
        fh.write(body)
    os.replace(dest + ".tmp", dest)
    audit(dirpath, "fetch", no_audit, number=name, source="patentimages", ok=True, doc="pdf", url=url,
          bytes=len(body))
    out.update({"status": "fetched", "path": dest, "url": url, "message": "PDF link from %s" % how})
    return out


def locate_in_cache(dirpath, number, quote, context=None):
    """Offline lookup for other scripts (quote_check.py): never touches the network."""
    p = find_pdf(dirpath, number)
    if not p:
        return _not_found("grant PDF not cached; run colline.py fetch %s" % number, pdf=None)
    return locate(p, quote, context=context)


# --------------------------------------------------------------------------- annotate


def _is_us_grant(number):
    norm = normalize(number or "")
    return bool(norm.get("ok")) and norm["country"] == "US" and norm["doc_type"] in GRANT_TYPES


def _context_for(dirpath, number, pinpoint, rec_cache):
    if not pinpoint or not SYNTHETIC_PIN.match(pinpoint):
        return None
    if number not in rec_cache:
        try:
            from patent_fetch import find_cached
            rec_cache[number] = find_cached(dirpath, number)[1]
        except Exception:
            rec_cache[number] = None
    rec = rec_cache[number]
    for p in (rec or {}).get("description") or []:
        if p.get("label") == pinpoint or p.get("pid") == pinpoint:
            return p.get("text")
    return None


def _annotate_entry(entry, where, number, a, res, pdf_cache, rec_cache):
    s = res["summary"]
    s["candidates"] += 1
    if number not in pdf_cache:
        try:
            r = fetch_pdf(a.dir, number, offline=a.offline, no_audit=a.no_audit)
        except UsageError as e:
            r = {"status": "bad_input", "message": str(e)}
        pdf_cache[number] = r
        if r["status"] == "network_error":
            res["_network_error"] = True
    r = pdf_cache[number]
    if not r.get("path"):
        s["no_pdf"] += 1
        res["findings"].append(finding("WARN", "pdf_unavailable", where, "%s: %s" % (number, r.get("message")
                                                                                     or r["status"])))
        return False
    ctx = _context_for(a.dir, number, entry.get("pinpoint"), rec_cache)
    loc = locate(r["path"], entry.get("quote"), context=ctx)
    before = json.dumps(entry, sort_keys=True)
    if loc["found"] and loc["confidence"] == "high":
        old = entry.get("pinpoint_colline")
        entry["pinpoint_colline"] = loc["pinpoint"]
        entry.pop("pinpoint_colline_candidate", None)
        s["filled"] += 1
        if old and old != loc["pinpoint"]:
            res["findings"].append(finding("INFO", "colline_changed", where, "%s -> %s" % (old, loc["pinpoint"])))
        res["text"].append("%-40s %s  (page %d, score %.2f)" % (where, loc["pinpoint"], loc["page"], loc["score"]))
    elif loc["found"]:
        entry.pop("pinpoint_colline", None)
        entry["pinpoint_colline_candidate"] = loc["pinpoint"]
        s["low"] += 1
        res["findings"].append(finding("WARN", "colline_low_confidence", where,
                                       "%s (page %d) is low confidence: %s; check the PDF"
                                       % (loc["pinpoint"], loc["page"], "; ".join(loc["reasons"]))))
    else:
        s["not_found"] += 1
        if entry.pop("pinpoint_colline", None) is not None:
            res["findings"].append(finding("WARN", "colline_removed", where, "stale pinpoint_colline removed"))
        entry.pop("pinpoint_colline_candidate", None)
        res["findings"].append(finding("WARN", "colline_not_found", where, "%s: %s" % (number, loc["reason"])))
    changed = json.dumps(entry, sort_keys=True) != before
    audit(a.dir, "quote", a.no_audit, where=where, number=number, result="colline",
          pinpoint_colline=loc.get("pinpoint"), confidence=loc.get("confidence"),
          score=loc.get("score"), written=bool(changed and not a.dry_run))
    return changed


def _resolve(path, dirpath):
    if os.path.exists(path):
        return path
    alt = os.path.join(dirpath, path)
    if os.path.exists(alt):
        return alt
    raise UsageError("file not found: %s" % path)


def run_annotate(a, res):
    res["summary"] = {"candidates": 0, "filled": 0, "low": 0, "not_found": 0, "no_pdf": 0, "skipped": 0}
    pdf_cache, rec_cache = {}, {}
    pa_path = None
    if a.from_file:
        pa_path = _resolve(a.from_file, a.dir)
        if os.path.isdir(pa_path):
            pa_path = os.path.join(pa_path, "prior-art.json")
    elif not a.chart:
        cand = os.path.join(a.dir, "prior-art.json")
        pa_path = cand if os.path.exists(cand) else None
    pa = check_schema(read_json(pa_path), SCHEMA_PRIOR_ART, pa_path) if pa_path else None
    refs_src = pa
    if refs_src is None and os.path.exists(os.path.join(a.dir, "prior-art.json")):
        refs_src = read_json(os.path.join(a.dir, "prior-art.json"))  # chart refs may only name an id
    refs_by_id = {r.get("id"): r for r in (refs_src or {}).get("references") or []}

    def eligible(entry, number):
        if not isinstance(entry, dict) or not entry.get("quote"):
            return False
        pin = entry.get("pinpoint")
        if pin and not SYNTHETIC_PIN.match(str(pin)):
            return False
        return _is_us_grant(number)

    if pa is not None:
        res["checks_run"].append("prior-art element_map (%s)" % pa_path)
        changed = False
        for ref in pa.get("references") or []:
            for el, entry in sorted((ref.get("element_map") or {}).items()):
                number = (entry.get("source_number") or ref.get("number")) if isinstance(entry, dict) else None
                if not eligible(entry, number):
                    if isinstance(entry, dict) and entry.get("quote"):
                        res["summary"]["skipped"] += 1
                    continue
                if _annotate_entry(entry, "prior-art %s.%s" % (ref.get("id"), el), number, a, res,
                                   pdf_cache, rec_cache):
                    changed = True
        if changed and not a.dry_run:
            write_json(pa_path, pa)

    chart_files = []
    if a.chart:
        chart_files = [_resolve(a.chart, a.dir)]
    elif not a.from_file:
        chart_files = sorted(glob.glob(os.path.join(a.dir, "charts", "*.json")))
    if chart_files:
        res["checks_run"].append("chart cells")
    for path in chart_files:
        chart = check_schema(read_json(path), SCHEMA_CHART, path)
        crefs = {r.get("id"): r for r in chart.get("refs") or []}
        changed = False
        for i, cell in enumerate(chart.get("cells") or []):
            rid = cell.get("ref")
            number = cell.get("source_number") or (crefs.get(rid) or {}).get("number") or \
                (refs_by_id.get(rid) or {}).get("number")
            if not eligible(cell, number):
                if cell.get("quote"):
                    res["summary"]["skipped"] += 1
                continue
            where = "%s cell %d (%s x %s)" % (os.path.basename(path), i, cell.get("element"), rid)
            if _annotate_entry(cell, where, number, a, res, pdf_cache, rec_cache):
                changed = True
        if changed and not a.dry_run:
            write_json(path, chart)
    if pa is None and not chart_files:
        raise UsageError("nothing to annotate: give --from prior-art.json or --chart charts/X.json")
    s = res["summary"]
    res["text"].append("colline: %d candidate quotes, %d filled (high), %d low (candidate only), %d not found, "
                       "%d without PDF, %d skipped (not a US grant or pinpoint already printed)"
                       % (s["candidates"], s["filled"], s["low"], s["not_found"], s["no_pdf"], s["skipped"]))
    if a.dry_run:
        res["text"].append("dry run: no files written")
    if res.pop("_network_error", False):
        res["exit_code"] = 3


# --------------------------------------------------------------------------- run / CLI


DEFAULTS = {"command": None, "dir": "patent", "json": False, "no_audit": False, "offline": False,
            "numbers": [], "number": None, "quote": None, "pdf": None, "context": None, "force": False,
            "file": None, "from_file": None, "chart": None, "dry_run": False}


def _pdf_for(a, res):
    if a.pdf:
        if not os.path.exists(a.pdf):
            raise UsageError("--pdf not found: %s" % a.pdf)
        return a.pdf
    if not a.number:
        raise UsageError("give a patent number (or --pdf)")
    r = fetch_pdf(a.dir, a.number, offline=a.offline, no_audit=a.no_audit)
    if r["status"] == "network_error":
        raise SourceError(r["message"])
    if not r.get("path"):
        res["exit_code"] = 3 if r["status"] == "not_cached" else 1
        res["findings"].append(finding("BLOCK", "pdf_unavailable", a.number, r.get("message") or r["status"]))
        return None
    return r["path"]


def run(args):
    a = to_namespace(args, DEFAULTS)
    res = new_result()
    res["command"] = a.command
    if a.command == "fetch":
        nums = list(a.numbers or ([a.number] if a.number else []))
        if not nums:
            raise UsageError("give at least one patent number")
        if a.file and len(nums) != 1:
            raise UsageError("--file imports one PDF for one number")
        res["checks_run"].append("grant PDF fetch")
        results = []
        for n in nums:
            r = fetch_pdf(a.dir, n, offline=a.offline, force=a.force, file=a.file, no_audit=a.no_audit)
            results.append(r)
            res["text"].append("%-16s %-10s %s" % (n, r["status"], r.get("path") or r.get("message") or ""))
            if r["status"] in ("not_found", "not_cached", "network_error"):
                res["findings"].append(finding("BLOCK" if r["status"] == "not_found" else "WARN", r["status"], n,
                                               r.get("message") or r["status"]))
        res["results"] = results
        st = [r["status"] for r in results]
        res["summary"] = {"requested": len(st), "fetched": st.count("fetched") + st.count("imported"),
                          "cached": st.count("cached"), "failed": len(st) - st.count("fetched")
                          - st.count("imported") - st.count("cached")}
        if "network_error" in st or "not_cached" in st:
            res["exit_code"] = 3
        return finalize(res)
    if a.command == "locate":
        if not a.quote:
            raise UsageError("give the quote text")
        if a.number:
            _check_grant(a.number)
        path = _pdf_for(a, res)
        if path is None:
            return finalize(res)
        res["checks_run"].append("column:line locate")
        loc = locate(path, a.quote, context=a.context)
        res.update(loc)
        res["summary"] = {"found": loc["found"], "confidence": loc["confidence"]}
        if loc["found"]:
            res["text"].append("%s  (page %d%s, confidence %s, score %.3f)" % (
                loc["pinpoint"], loc["page"], "-%d" % loc["end_page"] if loc["end_page"] != loc["page"] else "",
                loc["confidence"], loc["score"]))
            res["text"].append("  matched: %s" % loc["matched_text"])
            if loc["also"]:
                res["text"].append("  also at: %s" % "; ".join(loc["also"]))
            for note in loc["reasons"]:
                if note.startswith("note:"):
                    res["text"].append("  " + note)
            if loc["confidence"] == "low":
                res["findings"].append(finding("WARN", "colline_low_confidence", a.number or path,
                                               "; ".join(loc["reasons"])))
        else:
            res["findings"].append(finding("BLOCK", "colline_not_found", a.number or path, loc["reason"]))
            if loc.get("closest"):
                res["text"].append("closest (%.2f) at %s: %s" % (loc["closest"]["score"], loc["closest"]["pinpoint"],
                                                                loc["closest"]["text"]))
        audit(a.dir, "quote", a.no_audit, number=a.number, result="colline", pinpoint_colline=loc.get("pinpoint"),
              confidence=loc.get("confidence"), score=loc.get("score"))
        return finalize(res)
    if a.command == "layout":
        path = _pdf_for(a, res)
        if path is None:
            return finalize(res)
        lay = get_layout(path)
        res["checks_run"].append("layout")
        res["layout"] = {"pdf": path, "page_count": lay["page_count"], "spec_pages": lay["spec_pages"],
                         "problems": lay["problems"], "col_offset_support": lay.get("col_offset_support")}
        res["text"].append("%s: %d pages, %d specification pages" % (path, lay["page_count"], len(lay["spec_pages"])))
        for sp in lay["spec_pages"]:
            res["text"].append("  page %-3d cols %d-%d (%s, read %s)  grid %s n=%d pitch=%.2f line1_y=%.1f  words %s"
                               % (sp["page"], sp["columns"][0], sp["columns"][1], sp["columns_source"],
                                  sp["printed_numerals"], sp["grid_source"], sp["markers"], sp["pitch"],
                                  sp["line1_y"], sp["words"]))
        for p in lay["problems"]:
            res["findings"].append(finding("BLOCK", "no_layout", path, p))
        return finalize(res)
    if a.command == "annotate":
        run_annotate(a, res)
        return finalize(res)
    raise UsageError("command must be fetch, locate, layout, or annotate")


def build_parser():
    p = argparse.ArgumentParser(prog="colline.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__.split("\n\n", 1)[1])
    add_common(p, network=True)
    sp = p.add_subparsers(dest="command")
    f = sp.add_parser("fetch", help="download grant PDFs into <dir>/cache/pdf/")
    add_common(f, sub=True, network=True)
    f.add_argument("numbers", nargs="+")
    f.add_argument("--force", action="store_true", help="re-download even if cached")
    f.add_argument("--file", default=None, help="import this local PDF instead of downloading")
    lo = sp.add_parser("locate", help="map a quote to col:line")
    add_common(lo, sub=True, network=True)
    lo.add_argument("number", nargs="?", default=None)
    lo.add_argument("quote")
    lo.add_argument("--pdf", default=None, help="use this PDF instead of the cache")
    lo.add_argument("--context", default=None, help="surrounding paragraph text, to choose among repeats")
    la = sp.add_parser("layout", help="show detected specification pages, columns, and line grids")
    add_common(la, sub=True, network=True)
    la.add_argument("number", nargs="?", default=None)
    la.add_argument("--pdf", default=None)
    an = sp.add_parser("annotate", help="fill pinpoint_colline in prior-art.json / chart cells")
    add_common(an, sub=True, network=True)
    an.add_argument("--from", dest="from_file", default=None, help="prior-art.json (or matter dir)")
    an.add_argument("--chart", default=None, help="one chart file")
    an.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    return p


def main(argv=None):
    return cli_main(build_parser, run, argv)


if __name__ == "__main__":
    sys.exit(main())
