#!/usr/bin/env python3
"""build_docx.py - spec.md + claims.md -> Patent Center-ready DOCX.

Usage:
  python3 scripts/build_docx.py --spec draft/spec.md --claims draft/claims.md --out draft/out/
         [--split] [--provisional] [--font "Times New Roman"] [--size 12] [--spacing 1.5|2]
         [--claims-heading "WHAT IS CLAIMED IS:"] [--pdf-check] [--dir patent] [--json] [--no-audit]

Writes spec.docx (one multi-section document) or, with --split, specification.docx, claims.docx and
abstract.docx (Patent Center accepts either form).

Rules encoded:
  37 CFR 1.52(a)(1)(ii)  letter or A4; margins top >= 2.0 cm, left >= 2.5 cm, right >= 2.0 cm,
                         bottom >= 2.0 cm. We use 1 inch (2.54 cm) on every side.
  37 CFR 1.52(b)(2)      1.5 or double line spacing; nonscript font, capitals >= 0.21 cm (12 pt preferred);
                         single column.
  37 CFR 1.52(b)(3), 1.75(h)  claims start on a new page.
  37 CFR 1.52(b)(4), 1.72(b)  abstract starts on a new page; one paragraph; <= 150 words.
  37 CFR 1.52(b)(5)      pages numbered consecutively from 1, centered below the text.
  37 CFR 1.52(b)(6)      spec paragraphs (not claims/abstract) numbered [0001] in bold, ~4 spaces after;
                         headings are not numbered; lists and tables belong to the paragraph above them.
  37 CFR 1.72(a)         title at the top of the first page; <= 500 characters.
  37 CFR 1.75(i)         each claim element on its own indented line.
  USPTO DOCX guidance    fonts from the Patent Center supported-fonts list (Master File, March 2026);
                         headings uppercase, not bold (DOCX best practices; references/forms-and-filing.md);
                         no comments, tracked changes, embedded objects or images in the text;
                         section headers Patent Center recognises: "WHAT IS CLAIMED IS" / "CLAIMS",
                         "ABSTRACT" (docx-section-headers list, May 2025).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple

# Patent Center supported DOCX fonts (USPTO "Master File-PROD-Fonts-March-2026", lower-cased family names)
SUPPORTED_FONTS = {
    "aptos", "aptos black", "aptos display", "aptos extra", "aptos light", "aptos mono", "aptos narrow",
    "aptos semi", "arial", "arial black", "arial narrow", "arial rounded mt", "arial unicode ms", "batang",
    "batangche", "bierstadt", "bierstadt display", "calibri", "cambria", "cambria math", "castellar",
    "century", "century gothic", "century schoolbook", "courier new", "georgia", "liberation",
    "liberation sans", "lucida sans", "ms mincho", "ms pmincho", "mingliu extb", "monaco", "pmingliu extb",
    "pmingliu", "stixgeneral", "segoe ui symbol", "simsun", "symbol", "tahoma", "times", "times new roman",
    "times-new-roman", "trebuchet ms", "verdana", "wide latin", "dengxian", "new gulim", "biz udgothic",
    "hysinmyeongjo-medium", "timesnewromanpsmt", "helvetica", "calibri light",
}
# 1.52(b)(2)(ii) "nonscript type font"; decorative faces on the USPTO list we still steer away from
NOT_RECOMMENDED = {"castellar", "wide latin", "symbol", "segoe ui symbol", "cambria math"}

NO_NUMBER_SECTIONS = ("TITLE",)
CLAIM_HEADS = ("CLAIMS", "WHAT IS CLAIMED", "I CLAIM", "WE CLAIM", "CLAIMED IS")
ABSTRACT_HEADS = ("ABSTRACT",)
LEFTOVER_RE = re.compile(r"\[(?:ask user|TODO|TBD|todo|tbd)\]|\bTODO\b|\bTBD\b|\bXXX\b|\?\?\?|<<|>>")


class UsageError(Exception):
    pass


def _docx():
    try:
        import docx  # noqa
        return docx
    except ImportError:
        raise UsageError("python-docx is not installed: pip install python-docx")


# --------------------------------------------------------------------------- markdown -> blocks

def split_sections(md: str) -> List[Tuple[str, List[str]]]:
    out = []
    cur, buf = None, []
    in_comment = False
    for line in md.splitlines():
        m = re.match(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m and not in_comment:
            if cur is not None or any(l.strip() for l in buf):
                out.append((cur or "", buf))
            cur, buf = m.group(2).strip(), []
            continue
        buf.append(line)
    out.append((cur or "", buf))
    return out


def strip_comments(text: str, notes: List[str]) -> str:
    def repl(m):
        notes.append(m.group(0)[:60])
        return ""
    return re.sub(r"<!--.*?-->", repl, text, flags=re.S)


def blocks_of(lines: List[str]) -> List[dict]:
    """Group body lines into blocks: para, list, table, code."""
    blocks = []
    para = []
    i = 0

    def flush():
        if para:
            blocks.append({"kind": "para", "text": " ".join(s.strip() for s in para)})
            para[:] = []
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("```"):
            flush()
            j = i + 1
            code = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                code.append(lines[j].rstrip())
                j += 1
            blocks.append({"kind": "code", "lines": code})
            i = j + 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            i += 1
            continue
        if s.startswith("|") and s.count("|") >= 2:
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                r = lines[i].strip().strip("|")
                if not re.match(r"^\s*:?-{2,}", r.split("|")[0] if "|" in r else r):
                    rows.append([c.strip() for c in r.split("|")])
                i += 1
            blocks.append({"kind": "table", "rows": rows})
            continue
        m = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", s)
        if m and not para:
            items = []
            while i < len(lines):
                s2 = lines[i].strip()
                m2 = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", s2)
                if m2:
                    items.append(m2.group(2))
                elif s2 and items and lines[i].startswith((" ", "\t")):
                    items[-1] += " " + s2
                else:
                    break
                i += 1
            blocks.append({"kind": "list", "items": items})
            continue
        if s.startswith(">"):
            s = s.lstrip("> ").strip()
        para.append(s)
        i += 1
    flush()
    return blocks


_INLINE = re.compile(r"(\*\*[^*]+\*\*|__[^_]+__|\*[^*\s][^*]*\*|(?<![\w])_[^_\s][^_]*_(?![\w])|`[^`]+`)")


def inline_runs(text: str) -> List[Tuple[str, bool, bool]]:
    """Markdown inline -> [(text, bold, italic)]. Links keep their text; images and HTML tags are dropped."""
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"</?[A-Za-z][^>]*>", "", t)
    t = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|])", r"\1", t)
    out = []
    pos = 0
    for m in _INLINE.finditer(t):
        if m.start() > pos:
            out.append((t[pos:m.start()], False, False))
        tok = m.group(0)
        if tok.startswith("**") or tok.startswith("__"):
            out.append((tok[2:-2], True, False))
        elif tok.startswith("`"):
            out.append((tok[1:-1], False, False))
        else:
            out.append((tok[1:-1], False, True))
        pos = m.end()
    if pos < len(t):
        out.append((t[pos:], False, False))
    return [(re.sub(r"\s+", " ", a), b, c) for a, b, c in out if a]


def plain(text: str) -> str:
    return "".join(a for a, _, _ in inline_runs(text))


# --------------------------------------------------------------------------- claims parsing

def parse_claims(text: str) -> List[dict]:
    """claims.md -> [{num, first, elements:[...]}]. A number at line start begins a new claim."""
    claims = []
    cur = None
    for raw in text.splitlines():
        if re.match(r"^\s{0,3}#", raw):
            continue
        s = raw.rstrip()
        m = re.match(r"^\s{0,3}(\d+)\s*[.)]\s+(.*)$", s)
        if m:
            cur = {"num": int(m.group(1)), "first": m.group(2).strip(), "elements": [], "_cont": False}
            claims.append(cur)
            continue
        if cur is None or not s.strip():
            if cur is not None and not s.strip():
                cur["_cont"] = False
            continue
        if raw.startswith((" ", "\t")):
            cur["elements"].append(s.strip())
        elif cur["elements"]:
            cur["elements"][-1] += " " + s.strip()
        else:
            cur["first"] += " " + s.strip()
    for c in claims:
        c.pop("_cont", None)
    return claims


# --------------------------------------------------------------------------- docx writing

def _set_font(docx, style_or_run_element, font: str, size_pt: Optional[float] = None):
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    rpr = style_or_run_element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for att in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(att), font)
    for att in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rfonts.get(qn(att)) is not None:
            del rfonts.attrib[qn(att)]


def new_document(font: str, size: float, spacing: float):
    docx = _docx()
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_LINE_SPACING
    from docx.oxml.ns import qn
    d = docx.Document()
    # privacy: python-docx's template carries author/description text
    cp = d.core_properties
    cp.author = ""
    cp.last_modified_by = ""
    cp.comments = ""
    cp.title = ""
    cp.subject = ""
    cp.keywords = ""
    cp.category = ""
    for s in d.sections:
        s.page_width = Inches(8.5)          # letter, 1.52(a)(1)(ii)
        s.page_height = Inches(11)
        s.left_margin = Inches(1)           # >= 2.5 cm
        s.right_margin = Inches(1)          # >= 2.0 cm
        s.top_margin = Inches(1)            # >= 2.0 cm
        s.bottom_margin = Inches(1)         # >= 2.0 cm
        s.header_distance = Inches(0.5)
        s.footer_distance = Inches(0.5)
    st = d.styles["Normal"]
    st.font.name = font
    st.font.size = Pt(size)
    _set_font(docx, st.element, font)
    pf = st.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE if spacing < 1.75 else WD_LINE_SPACING.DOUBLE
    pf.space_before = Pt(0)
    pf.space_after = Pt(6)
    # document defaults too, so nothing falls back to a theme font
    rpr_default = d.styles.element.find(qn("w:docDefaults"))
    if rpr_default is not None:
        r = rpr_default.find(qn("w:rPrDefault"))
        if r is not None and r.find(qn("w:rPr")) is not None:
            rp = r.find(qn("w:rPr"))
            rf = rp.find(qn("w:rFonts"))
            if rf is not None:
                for att in list(rf.attrib):
                    del rf.attrib[att]
                for att in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                    rf.set(qn(att), font)
    _page_number_footer(d)
    return d


def _page_number_footer(d):
    """Centered PAGE field in the footer, 1.52(b)(5). Headers stay empty."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    for s in d.sections:
        p = s.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run()
        b = OxmlElement("w:fldChar")
        b.set(qn("w:fldCharType"), "begin")
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = " PAGE "
        sep = OxmlElement("w:fldChar")
        sep.set(qn("w:fldCharType"), "separate")
        t = OxmlElement("w:t")
        t.text = "1"
        e = OxmlElement("w:fldChar")
        e.set(qn("w:fldCharType"), "end")
        for el in (b, it, sep, t, e):
            r._r.append(el)


def add_heading(d, text: str, page_break: bool = False):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    if page_break:
        p.paragraph_format.page_break_before = True
    # USPTO DOCX best practices: headings uppercase, not bold, not underlined; Patent Center
    # splits the document on recognized headings, which must be the first line of their section
    p.add_run(text.upper())
    return p


def add_runs(p, text: str):
    # Markdown bold is dropped (only paragraph numbers are bold, 1.52(b)(6)); italics are kept
    # for terms such as Latin names
    for (t, b, i) in inline_runs(text):
        r = p.add_run(t)
        if i:
            r.italic = True


def add_numbered(d, n: int, text: str):
    p = d.add_paragraph()
    lab = p.add_run("[%04d]" % n)
    lab.bold = True                       # 1.52(b)(6): number in bold
    p.add_run("    ")                     # ~four spaces after the number
    add_runs(p, text)
    return p


def add_plain(d, text: str, indent_in: float = 0.0, align=None):
    from docx.shared import Inches
    p = d.add_paragraph()
    if indent_in:
        p.paragraph_format.left_indent = Inches(indent_in)
    if align is not None:
        p.alignment = align
    add_runs(p, text)
    return p


def add_table(d, rows: List[List[str]]):
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    t = d.add_table(rows=len(rows), cols=ncol)
    t.style = d.styles["Table Grid"] if "Table Grid" in [s.name for s in d.styles] else None
    for i, r in enumerate(rows):
        for j in range(ncol):
            cell = t.cell(i, j)
            cell.text = ""
            add_runs(cell.paragraphs[0], r[j] if j < len(r) else "")


def write_claims(d, claims: List[dict], heading: str, page_break: bool):
    from docx.enum.text import WD_BREAK
    add_heading(d, heading, page_break=page_break)
    for c in claims:
        p = d.add_paragraph()
        add_runs(p, "%d. %s" % (c["num"], c["first"]))
        for el in c["elements"]:
            # one paragraph per claim; each element on its own indented line, 1.75(i)
            p.add_run().add_break(WD_BREAK.LINE)
            p.add_run("\t")
            add_runs(p, el)


def write_abstract(d, text: str, page_break: bool):
    add_heading(d, "ABSTRACT", page_break=page_break)
    add_plain(d, text)


# --------------------------------------------------------------------------- build

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_pages(docx_path: str, findings: List[dict]) -> Optional[int]:
    soffice = shutil.which("soffice") or ("/opt/homebrew/bin/soffice" if os.path.exists("/opt/homebrew/bin/soffice")
                                          else None) or (
        "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if os.path.exists("/Applications/LibreOffice.app/Contents/MacOS/soffice") else None)
    if not soffice:
        findings.append({"level": "INFO", "code": "pdf-check-skipped", "where": docx_path,
                         "message": "LibreOffice (soffice) not found; page count not measured"})
        return None
    tmp = tempfile.mkdtemp(prefix="pa-docx-")
    try:
        prof = "file://" + os.path.join(tmp, "profile")
        subprocess.run([soffice, "-env:UserInstallation=" + prof, "--headless", "--convert-to", "pdf",
                        "--outdir", tmp, docx_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=180, check=False)
        pdf = os.path.join(tmp, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
        if not os.path.exists(pdf):
            findings.append({"level": "INFO", "code": "pdf-check-failed", "where": docx_path,
                             "message": "soffice did not produce a PDF; page count not measured"})
            return None
        try:
            from pypdf import PdfReader
            return len(PdfReader(pdf).pages)
        except ImportError:
            data = open(pdf, "rb").read()
            return len(re.findall(rb"/Type\s*/Page[^s]", data))
    except (OSError, subprocess.SubprocessError) as ex:
        findings.append({"level": "INFO", "code": "pdf-check-failed", "where": docx_path, "message": str(ex)})
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build(spec_path: str, claims_path: Optional[str], out_dir: str, split: bool = False,
          provisional: bool = False, font: str = "Times New Roman", size: float = 12.0,
          spacing: float = 1.5, claims_heading: str = "WHAT IS CLAIMED IS:", pdf_check: bool = False) -> dict:
    findings = []

    def add(level, code, where, msg):
        findings.append({"level": level, "code": code, "where": where, "message": msg})
    fl = font.strip().lower()
    if fl not in SUPPORTED_FONTS:
        raise UsageError("font %r is not on Patent Center's supported DOCX font list (e.g., Times New Roman, "
                         "Arial, Calibri, Courier New, Georgia)" % font)
    if fl in NOT_RECOMMENDED:
        add("WARN", "font-style", "font", "%s is decorative; 37 CFR 1.52(b)(2)(ii) wants a plain nonscript font" % font)
    if size < 6.0:
        raise UsageError("font size below 6 pt fails 37 CFR 1.52(b)(2)(ii) (capitals >= 0.21 cm)")
    if size < 11.0:
        add("WARN", "font-size", "font", "%.1f pt is legal but 12 pt is preferred (37 CFR 1.52(b)(2)(ii))" % size)
    if spacing not in (1.5, 2.0):
        raise UsageError("line spacing must be 1.5 or 2 (37 CFR 1.52(b)(2)(i))")
    with open(spec_path, "r", encoding="utf-8") as fh:
        spec_md = fh.read()
    notes = []
    spec_md = strip_comments(spec_md, notes)
    for nt in notes:
        add("WARN", "comment-stripped", "spec.md", "HTML comment removed from the filing copy: %r" % nt)
    secs = split_sections(spec_md)

    title = None
    body_secs = []
    claims_from_spec = None
    abstract = None
    for head, lines in secs:
        H = head.upper().strip()
        if not H:
            if any(l.strip() for l in lines):
                add("WARN", "text-before-heading", "spec.md", "text before the first heading was left out")
            continue
        if H.startswith("SPECIFICATION") and not any(l.strip() for l in lines):
            continue
        if H.startswith("TITLE"):
            tl = [l.strip() for l in lines if l.strip()]
            title = plain(tl[0]) if tl else None
            continue
        if any(H.startswith(k) for k in CLAIM_HEADS):
            txt = "\n".join(lines)
            cl = parse_claims(txt)
            if cl:
                claims_from_spec = cl
            continue
        if any(H.startswith(k) for k in ABSTRACT_HEADS):
            bl = blocks_of(lines)
            paras = [b["text"] for b in bl if b["kind"] == "para"] + \
                    [" ".join(b["items"]) for b in bl if b["kind"] == "list"]
            if len(paras) > 1:
                add("WARN", "abstract-joined", "ABSTRACT",
                    "abstract had %d paragraphs; joined into one (37 CFR 1.72(b))" % len(paras))
            abstract = " ".join(paras).strip() or None
            continue
        body_secs.append((H, blocks_of(lines)))

    claims = None
    if claims_path:
        if not os.path.exists(claims_path):
            raise UsageError("claims file not found: %s" % claims_path)
        with open(claims_path, "r", encoding="utf-8") as fh:
            cmd = strip_comments(fh.read(), notes)
        claims = parse_claims(cmd) or None
    if claims is None:
        claims = claims_from_spec
    if not claims:
        if provisional:
            add("INFO", "no-claims", "claims", "provisional built without claims (allowed: 35 U.S.C. 111(b)(2)); "
                                               "claims are still recommended")
        else:
            add("BLOCK", "no-claims", "claims", "a nonprovisional needs at least one claim (35 U.S.C. 112(b), "
                                                "37 CFR 1.75); pass --provisional for a provisional")
    else:
        nums = [c["num"] for c in claims]
        if nums != list(range(1, len(nums) + 1)):
            add("BLOCK", "claim-numbering", "claims", "claims must be numbered consecutively from 1 "
                                                       "(37 CFR 1.126); found %s" % nums)
    if title is None:
        add("WARN", "no-title", "spec.md", "no ## TITLE section; the title must be at the top of the first page "
                                           "unless given in the ADS (37 CFR 1.72(a))")
    elif len(title) > 500:
        add("BLOCK", "title-long", "TITLE", "title is %d characters; limit is 500 (37 CFR 1.72(a))" % len(title))
    if abstract is None:
        if provisional:
            add("INFO", "no-abstract", "ABSTRACT", "no abstract (optional for a provisional)")
        else:
            add("BLOCK", "no-abstract", "ABSTRACT", "a nonprovisional needs an abstract (37 CFR 1.72(b))")
    else:
        wc = len(plain(abstract).split())
        if wc > 150:
            add("BLOCK", "abstract-long", "ABSTRACT", "abstract has %d words; limit is 150 (37 CFR 1.72(b))" % wc)
        elif wc < 50:
            add("WARN", "abstract-short", "ABSTRACT", "abstract has %d words; Patent Center warns under 50 "
                                                      "(DOCX warning 3062)" % wc)
        legal = sorted(set(w.lower() for w in re.findall(r"\b(means|said)\b", plain(abstract), re.I)))
        if legal:
            add("WARN", "abstract-legal-words", "ABSTRACT", "avoid %s in the abstract (MPEP 608.01(b); "
                                                            "DOCX warning 3063)" % ", ".join(repr(w) for w in legal))
    if not body_secs:
        raise UsageError("spec.md has no sections (expected ## BACKGROUND, ## DETAILED DESCRIPTION, ...)")

    # leftover drafting notes and images
    for H, bl in body_secs:
        for b in bl:
            txt = b.get("text") or " ".join(b.get("items", [])) or " ".join(" ".join(r) for r in b.get("rows", []))
            if b["kind"] == "para" and re.search(r"!\[[^\]]*\]\(", txt):
                add("WARN", "image-dropped", H, "Markdown image removed: figures go in the drawings, not the text")
            if txt and LEFTOVER_RE.search(txt):
                add("BLOCK", "leftover-note", H, "drafting note left in the text: %r" %
                    LEFTOVER_RE.search(txt).group(0))
            if b["kind"] == "code":
                add("WARN", "code-block", H, "code block written as plain lines; long program listings belong in "
                                            "a computer program listing appendix (37 CFR 1.96)")

    os.makedirs(out_dir, exist_ok=True)
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    counter = {"n": 0}

    def write_spec(d):
        if title:
            add_plain(d, title, align=WD_ALIGN_PARAGRAPH.CENTER)   # 1.72(a): title heads the first page
        for H, bl in body_secs:
            add_heading(d, H)
            for b in bl:
                if b["kind"] == "para":
                    counter["n"] += 1
                    add_numbered(d, counter["n"], b["text"])
                elif b["kind"] == "list":
                    # 1.52(b)(6): a list is part of the paragraph above it - no number of its own
                    if counter["n"] == 0:
                        counter["n"] += 1
                        add_numbered(d, counter["n"], b["items"][0])
                        items = b["items"][1:]
                    else:
                        items = b["items"]
                    for it in items:
                        add_plain(d, it, indent_in=0.5)
                elif b["kind"] == "table":
                    add_table(d, b["rows"])
                elif b["kind"] == "code":
                    for ln in b["lines"]:
                        add_plain(d, ln or " ", indent_in=0.5)

    outputs = []
    if split:
        d = new_document(font, size, spacing)
        write_spec(d)
        p1 = os.path.join(out_dir, "specification.docx")
        d.save(p1)
        outputs.append(p1)
        if claims:
            d = new_document(font, size, spacing)
            write_claims(d, claims, claims_heading, page_break=False)
            p2 = os.path.join(out_dir, "claims.docx")
            d.save(p2)
            outputs.append(p2)
        if abstract:
            d = new_document(font, size, spacing)
            write_abstract(d, abstract, page_break=False)
            p3 = os.path.join(out_dir, "abstract.docx")
            d.save(p3)
            outputs.append(p3)
    else:
        d = new_document(font, size, spacing)
        write_spec(d)
        if claims:
            write_claims(d, claims, claims_heading, page_break=True)
        if abstract:
            write_abstract(d, abstract, page_break=True)
        p = os.path.join(out_dir, "spec.docx")
        d.save(p)
        outputs.append(p)

    pages = None
    if pdf_check:
        pages = 0
        for o in outputs:
            n = pdf_pages(o, findings)
            if n is None:
                pages = None
                break
            pages += n
    summary = {
        "files": outputs,
        "paragraphs_numbered": counter["n"],
        "claims": len(claims or []),
        "independent_claims": sum(1 for c in (claims or []) if not re.search(r"\bclaim\s+\d+", c["first"], re.I)),
        "abstract_words": len(plain(abstract).split()) if abstract else 0,
        "title": title,
        "font": font, "size_pt": size, "spacing": spacing,
        "pages": pages,
    }
    if pages is not None:
        summary["size_fee_note"] = size_fee_note(pages, _drawing_sheets(out_dir))
    blocking = sum(1 for f in findings if f["level"] == "BLOCK")
    return {"ok": blocking == 0, "outputs": outputs, "findings": findings, "summary": summary}


def _drawing_sheets(out_dir: str) -> Optional[int]:
    """Number of drawing sheets from drawings-manifest.json next to the DOCX, if drawings were built."""
    try:
        with open(os.path.join(out_dir, "drawings-manifest.json"), "r", encoding="utf-8") as fh:
            return len(json.load(fh).get("sheets") or [])
    except (OSError, ValueError):
        return None


def size_fee_note(pages: int, drawing_sheets: Optional[int] = None) -> str:
    """Plain message about the application size fee (35 U.S.C. 41(a)(1)(G); 37 CFR 1.16(s)): it is due
    only above 100 sheets of spec + drawings, so say "Not due" when the count is under that."""
    total = pages + (drawing_sheets or 0)
    with_dr = (" + %d drawing sheet(s) = %d" % (drawing_sheets, total)) if drawing_sheets else ""
    if total <= 100:
        return ("%d pages%s; the size fee starts above 100 sheets (spec + drawings). Not due."
                % (pages, with_dr)) + ("" if drawing_sheets is not None else
                                       " (Drawing sheets count too; none were found in this folder.)")
    return ("%d pages%s; the size fee may be due: it is charged for each 50 sheets (or part) over 100 counted "
            "sheets of spec + drawings (37 CFR 1.16(s); e-filed sheets count at 75%%). Run fees.py --pages %d."
            % (pages, with_dr, total))


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
    """Tool entry point. args: {spec, claims?, out, split?, provisional?, font?, size?, spacing?,
    claims_heading?, pdf_check?, dir?, no_audit?}"""
    d = args.get("dir", "patent")
    spec = _resolve(args.get("spec") or "draft/spec.md", d)
    if not os.path.exists(spec):
        raise UsageError("spec file not found: %s" % spec)
    claims = args.get("claims")
    claims = _resolve(claims, d) if claims else None
    if claims and not os.path.exists(claims):
        if args.get("provisional"):
            claims = None
        else:
            raise UsageError("claims file not found: %s" % claims)
    out = args.get("out") or os.path.join(os.path.dirname(spec), "out")
    res = build(spec, claims, out, split=bool(args.get("split")), provisional=bool(args.get("provisional")),
                font=args.get("font") or "Times New Roman", size=float(args.get("size") or 12.0),
                spacing=float(args.get("spacing") or 1.5),
                claims_heading=args.get("claims_heading") or "WHAT IS CLAIMED IS:",
                pdf_check=bool(args.get("pdf_check")))
    for o in res["outputs"]:
        _audit(d, {"kind": "export", "path": o, "sha256": _sha256(o), "script": "build_docx.py"},
               bool(args.get("no_audit")))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build Patent Center-ready DOCX from spec.md and claims.md")
    ap.add_argument("--spec", default="draft/spec.md")
    ap.add_argument("--claims", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--split", action="store_true", help="write specification.docx, claims.docx, abstract.docx")
    ap.add_argument("--provisional", action="store_true", help="claims and abstract optional")
    ap.add_argument("--font", default="Times New Roman")
    ap.add_argument("--size", type=float, default=12.0)
    ap.add_argument("--spacing", type=float, default=1.5, choices=[1.5, 2.0])
    ap.add_argument("--claims-heading", default="WHAT IS CLAIMED IS:")
    ap.add_argument("--pdf-check", action="store_true", help="convert with LibreOffice to count pages")
    ap.add_argument("--dir", default="patent")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-audit", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = run({"spec": a.spec, "claims": a.claims, "out": a.out, "split": a.split, "provisional": a.provisional,
                   "font": a.font, "size": a.size, "spacing": a.spacing, "claims_heading": a.claims_heading,
                   "pdf_check": a.pdf_check, "dir": a.dir, "no_audit": a.no_audit})
    except UsageError as ex:
        print(json.dumps({"error": str(ex)}) if a.json else "error: %s" % ex,
              file=sys.stdout if a.json else sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for f in res["findings"]:
            print("%s  %s  %s  %s" % (f["level"], f["code"], f["where"], f["message"]))
        s = res["summary"]
        print("wrote: %s" % ", ".join(s["files"]))
        print("numbered paragraphs: %d; claims: %d; abstract words: %d; font: %s %.0f pt, %.1f spacing"
              % (s["paragraphs_numbered"], s["claims"], s["abstract_words"], s["font"], s["size_pt"], s["spacing"]))
        if s["pages"] is not None:
            print("pages (LibreOffice render): %s" % s["size_fee_note"])
        else:
            print("pages: not measured (use --pdf-check)")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
