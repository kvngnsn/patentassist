#!/usr/bin/env python3
"""Convert a Markdown report or memo into a Word (.docx) document.

    python3 scripts/md_to_docx.py report.md [-o report.docx] [--draft] [--dir patent] [--json] [--no-audit]

Adapted from startupassist/scripts/md_to_docx.py (MIT, same author), with generic
report styling: Times New Roman 12 pt, 1-inch margins, left-aligned body text,
bold headings (H1 centered), tables, bullet and numbered lists, block quotes as
shaded italic notes, fenced code in Courier New, and page numbers in the footer.
A Markdown horizontal rule ("---" on its own line) becomes a page break.
YAML front matter is dropped. --draft puts "DRAFT" in the page header.

This is for reports, memos, and charts. Patent Center filing copies are built by
build_docx.py, not this script.

Requires python-docx (pip install python-docx).
Exit codes: 0 ok, 2 usage or input error.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FONT = "Times New Roman"
INLINE_RE = re.compile(r"(\*\*\*.+?\*\*\*|\*\*.+?\*\*|\*(?!\s).+?\*|`.+?`)")
DRAFT_TEXT = "DRAFT - for review"


def _docx():
    try:
        import docx  # noqa: F401
        from docx import Document
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches, Pt, RGBColor
    except ImportError:
        return None
    return {"Document": Document, "WD_TABLE_ALIGNMENT": WD_TABLE_ALIGNMENT,
            "WD_ALIGN_PARAGRAPH": WD_ALIGN_PARAGRAPH, "WD_BREAK": WD_BREAK, "OxmlElement": OxmlElement,
            "qn": qn, "Inches": Inches, "Pt": Pt, "RGBColor": RGBColor}


def strip_front_matter(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            text = text[end + 4:]
    return text


def add_runs(D, par, text, italic=False):
    text = text.replace("\\*", "*").replace("\\_", "_").replace("\\|", "|")
    for piece in INLINE_RE.split(text):
        if not piece:
            continue
        if piece.startswith("***") and piece.endswith("***"):
            run = par.add_run(piece[3:-3]); run.bold = True; run.italic = True
        elif piece.startswith("**") and piece.endswith("**"):
            run = par.add_run(piece[2:-2]); run.bold = True
        elif piece.startswith("`") and piece.endswith("`"):
            run = par.add_run(piece[1:-1]); run.font.name = "Courier New"
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            run = par.add_run(piece[1:-1]); run.italic = True
        else:
            run = par.add_run(piece)
        if italic:
            run.italic = True


def shade(D, par, fill="EDEDED"):
    ppr = par._p.get_or_add_pPr()
    shd = D["OxmlElement"]("w:shd")
    shd.set(D["qn"]("w:val"), "clear")
    shd.set(D["qn"]("w:color"), "auto")
    shd.set(D["qn"]("w:fill"), fill)
    ppr.append(shd)


def add_page_number_footer(D, doc):
    for section in doc.sections:
        par = section.footer.paragraphs[0]
        par.alignment = D["WD_ALIGN_PARAGRAPH"].CENTER
        run = par.add_run()
        for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
            if tag:
                el = D["OxmlElement"]("w:fldChar"); el.set(D["qn"]("w:fldCharType"), tag)
            else:
                el = D["OxmlElement"]("w:instrText"); el.set(D["qn"]("xml:space"), "preserve"); el.text = text
            run._r.append(el)


def add_draft_header(D, doc):
    for section in doc.sections:
        par = section.header.paragraphs[0]
        par.alignment = D["WD_ALIGN_PARAGRAPH"].RIGHT
        run = par.add_run(DRAFT_TEXT)
        run.bold = True
        run.font.size = D["Pt"](10)
        run.font.color.rgb = D["RGBColor"](0x99, 0x00, 0x00)


def setup(D, doc):
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = D["Pt"](12)
    style.element.rPr.rFonts.set(D["qn"]("w:eastAsia"), FONT)
    style.paragraph_format.space_after = D["Pt"](8)
    style.paragraph_format.space_before = D["Pt"](0)
    for section in doc.sections:
        section.left_margin = section.right_margin = D["Inches"](1)
        section.top_margin = section.bottom_margin = D["Inches"](1)


def add_table(D, doc, rows):
    cells = [[c.strip() for c in re.split(r"(?<!\\)\|", r.strip().strip("|"))] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r if c)]
    if not cells:
        return
    width = max(len(r) for r in cells)
    table = doc.add_table(rows=len(cells), cols=width)
    table.style = "Table Grid"
    table.alignment = D["WD_TABLE_ALIGNMENT"].CENTER
    for i, row in enumerate(cells):
        for j in range(width):
            par = table.cell(i, j).paragraphs[0]
            par.paragraph_format.space_after = D["Pt"](2)
            add_runs(D, par, row[j] if j < len(row) else "")
            for run in par.runs:
                run.font.size = D["Pt"](10)
                if i == 0:
                    run.bold = True
    doc.add_paragraph()


def convert(md, draft=False):
    D = _docx()
    if D is None:
        raise RuntimeError("python-docx is required: pip install python-docx")
    doc = D["Document"]()
    setup(D, doc)
    Pt, Inches = D["Pt"], D["Inches"]
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                par = doc.add_paragraph()
                par.paragraph_format.space_after = Pt(0)
                run = par.add_run(lines[i]); run.font.name = "Courier New"; run.font.size = Pt(10)
                i += 1
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            doc.add_paragraph().add_run().add_break(D["WD_BREAK"].PAGE)
            i += 1
            continue

        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i]); i += 1
            add_table(D, doc, block)
            continue

        if stripped.startswith(">"):
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(lines[i].strip()[1:].strip()); i += 1
            par = doc.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.3)
            add_runs(D, par, " ".join(block), italic=True)
            shade(D, par)
            continue

        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            level, text = len(m.group(1)), m.group(2).strip().rstrip("#").strip()
            par = doc.add_paragraph()
            par.paragraph_format.keep_with_next = True
            par.paragraph_format.space_before = Pt(12 if level > 1 else 0)
            if level == 1:
                par.alignment = D["WD_ALIGN_PARAGRAPH"].CENTER
            add_runs(D, par, text)
            for run in par.runs:
                run.bold = True
                if level == 1:
                    run.font.size = Pt(14)
                elif level >= 3:
                    run.italic = True
            i += 1
            continue

        m = re.match(r"(\s*)([-*+]|\d+[.)])\s+(.*)", line)
        if m and not stripped.startswith("**"):
            indent = len(m.group(1).replace("\t", "    ")) // 2
            marker = "•" if m.group(2) in "-*+" else m.group(2)
            text = m.group(3)
            tm = re.match(r"\[( |x|X)\]\s+(.*)", text)
            if tm:
                marker = "☐" if tm.group(1) == " " else "☑"
                text = tm.group(2)
            par = doc.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.5 + 0.25 * indent)
            par.paragraph_format.first_line_indent = Inches(-0.25)
            par.paragraph_format.space_after = Pt(4)
            add_runs(D, par, "%s\t%s" % (marker, text))
            i += 1
            continue

        # Ordinary paragraph: join soft-wrapped lines until a blank line or block start.
        block = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or re.match(r"(#{1,6}\s|>|\||```|[-*+]\s|\d+[.)]\s|-{3,}$)", nxt):
                break
            if lines[i - 1].endswith("  ") or lines[i - 1].endswith("\\"):
                block.append("\n" + nxt)
            else:
                block.append(" " + nxt)
            i += 1
        text = "".join(block).replace("\\\n", "\n")
        par = doc.add_paragraph()
        for k, chunk in enumerate(text.split("\n")):
            if k:
                par.add_run().add_break()
            add_runs(D, par, chunk)
    if draft:
        add_draft_header(D, doc)
    add_page_number_footer(D, doc)
    return doc


def run(args):
    a = dict(vars(args)) if isinstance(args, argparse.Namespace) else dict(args or {})
    src = a.get("input")
    if not src or not os.path.exists(str(src)):
        return {"ok": False, "exit_code": 2, "error": "input not found: %s" % src}
    out = a.get("output") or os.path.splitext(str(src))[0] + ".docx"
    with open(str(src), encoding="utf-8") as fh:
        md = strip_front_matter(fh.read())
    try:
        convert(md, bool(a.get("draft"))).save(str(out))
    except RuntimeError as e:
        return {"ok": False, "exit_code": 2, "error": str(e)}
    d = a.get("dir") or "patent"
    if not a.get("no_audit") and os.path.isdir(d):
        try:
            from state import audit, sha256_path
            audit(d, "export", path=str(out), sha256=sha256_path(str(out)), script="md_to_docx.py")
        except Exception:
            pass
    return {"ok": True, "exit_code": 0, "output": str(out), "draft": bool(a.get("draft"))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output")
    ap.add_argument("--draft", action="store_true", help='put "DRAFT" in the page header')
    ap.add_argument("--dir", default="patent", help="matter folder for audit.jsonl (default: patent)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--no-audit", action="store_true", help="do not append to audit.jsonl")
    args = ap.parse_args(argv)
    res = run(args)
    if args.json:
        print(json.dumps(res, indent=2))
    elif res["ok"]:
        print("wrote %s" % res["output"])
    else:
        print("ERROR: %s" % res["error"], file=sys.stderr)
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
