"""Offline tests for scripts/build_docx.py (spec.md + claims.md -> Patent Center DOCX)."""

import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FIX = os.path.join(HERE, "fixtures", "build")
sys.path.insert(0, SCRIPTS)

import build_docx  # noqa: E402

try:
    import docx  # noqa: F401
    from docx.shared import Cm
    from docx.enum.text import WD_LINE_SPACING
    HAVE_DOCX = True
except ImportError:
    HAVE_DOCX = False

NUM_RE = re.compile(r"^\[(\d{4})\]")


@unittest.skipUnless(HAVE_DOCX, "python-docx not installed")
class BuildDocxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pa-docx-test-")
        self.res = build_docx.build(os.path.join(FIX, "spec.md"), os.path.join(FIX, "claims.md"), self.tmp)
        self.path = os.path.join(self.tmp, "spec.docx")
        self.doc = docx.Document(self.path)
        self.paras = self.doc.paragraphs

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _index(self, text):
        for i, p in enumerate(self.paras):
            if p.text.strip() == text:
                return i
        self.fail("paragraph %r not found" % text)

    def test_ok_and_summary(self):
        self.assertTrue(self.res["ok"], self.res["findings"])
        self.assertEqual(self.res["summary"]["claims"], 3)
        self.assertTrue(os.path.exists(self.path))

    def test_paragraph_numbering_consecutive_and_bold(self):
        nums = []
        for p in self.paras:
            m = NUM_RE.match(p.text)
            if m:
                nums.append(int(m.group(1)))
                self.assertEqual(p.runs[0].text, m.group(0))
                self.assertTrue(p.runs[0].bold, "paragraph number must be bold (37 CFR 1.52(b)(6))")
                self.assertTrue(p.text[6:10] == "    ", "about four spaces after the number")
        self.assertEqual(nums, list(range(1, len(nums) + 1)))
        self.assertEqual(len(nums), self.res["summary"]["paragraphs_numbered"])
        self.assertGreaterEqual(len(nums), 10)

    def test_headings_not_numbered_caps_not_bold(self):
        for h in ("BACKGROUND", "SUMMARY", "BRIEF DESCRIPTION OF THE DRAWINGS", "DETAILED DESCRIPTION"):
            p = self.paras[self._index(h)]
            self.assertFalse(NUM_RE.match(p.text))
            self.assertFalse(any(r.bold for r in p.runs), "%s heading should not be bold" % h)

    def test_title_first_and_unnumbered(self):
        first = next(p for p in self.paras if p.text.strip())
        self.assertEqual(first.text.strip(), "Helmet Turn-Signal System With Wireless Handlebar Remote")

    def test_claims_on_new_page_each_claim_own_paragraph(self):
        i = self._index("WHAT IS CLAIMED IS:")
        self.assertTrue(self.paras[i].paragraph_format.page_break_before)
        claims = [p for p in self.paras[i + 1:] if re.match(r"^\d+\. ", p.text)]
        self.assertEqual([p.text.split(".")[0] for p in claims], ["1", "2", "3"])
        # claim 1 keeps its four indented elements as line breaks inside the one paragraph
        brs = claims[0]._p.xpath(".//w:br")
        self.assertEqual(len(brs), 4)
        self.assertNotIn("[0", claims[0].text)

    def test_abstract_on_new_page_single_paragraph(self):
        i = self._index("ABSTRACT")
        self.assertTrue(self.paras[i].paragraph_format.page_break_before)
        rest = [p for p in self.paras[i + 1:] if p.text.strip()]
        self.assertEqual(len(rest), 1)
        self.assertTrue(rest[0].text.startswith("A helmet includes"))
        self.assertFalse(NUM_RE.match(rest[0].text))

    def test_font_margins_spacing_page(self):
        st = self.doc.styles["Normal"]
        self.assertEqual(st.font.name, "Times New Roman")
        self.assertEqual(st.font.size.pt, 12)
        self.assertIn(st.font.name.lower(), build_docx.SUPPORTED_FONTS)
        self.assertEqual(st.paragraph_format.line_spacing_rule, WD_LINE_SPACING.ONE_POINT_FIVE)
        rfonts = st.element.rPr.rFonts
        self.assertEqual(rfonts.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia"),
                         "Times New Roman")
        for s in self.doc.sections:
            self.assertAlmostEqual(s.page_width.inches, 8.5, places=2)
            self.assertAlmostEqual(s.page_height.inches, 11.0, places=2)
            self.assertGreaterEqual(s.left_margin, Cm(2.5))       # 37 CFR 1.52(a)(1)(ii)
            self.assertGreaterEqual(s.top_margin, Cm(2.0))
            self.assertGreaterEqual(s.right_margin, Cm(2.0))
            self.assertGreaterEqual(s.bottom_margin, Cm(2.0))

    def test_page_number_footer_and_clean_package(self):
        footer_xml = self.doc.sections[0].footer._element.xml
        self.assertIn("PAGE", footer_xml)
        header_text = "".join(p.text for p in self.doc.sections[0].header.paragraphs)
        self.assertEqual(header_text.strip(), "")
        with zipfile.ZipFile(self.path) as z:
            names = z.namelist()
            body = z.read("word/document.xml").decode("utf-8")
        self.assertNotIn("word/comments.xml", names)
        self.assertFalse(any(n.startswith("word/media/") for n in names), "no embedded images")
        self.assertNotIn("<w:ins ", body)
        self.assertNotIn("<w:del ", body)
        self.assertNotIn("w:object", body)
        self.assertEqual(self.doc.core_properties.author, "")

    def test_markdown_stripped_and_lists_unnumbered(self):
        text = "\n".join(p.text for p in self.paras)
        self.assertNotIn("**", text)
        self.assertNotIn("## ", text)
        self.assertIn("wireless link", text)
        lst = [p for p in self.paras if p.text.startswith("In one embodiment")]
        self.assertEqual(len(lst), 1)
        self.assertFalse(NUM_RE.match(lst[0].text), "a list belongs to the paragraph above (1.52(b)(6))")


@unittest.skipUnless(HAVE_DOCX, "python-docx not installed")
class BuildDocxModesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pa-docx-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_split_writes_three_files(self):
        res = build_docx.build(os.path.join(FIX, "spec.md"), os.path.join(FIX, "claims.md"), self.tmp, split=True)
        names = sorted(os.path.basename(p) for p in res["outputs"])
        self.assertEqual(names, ["abstract.docx", "claims.docx", "specification.docx"])
        d = docx.Document(os.path.join(self.tmp, "claims.docx"))
        self.assertEqual(d.paragraphs[0].text, "WHAT IS CLAIMED IS:")

    def test_provisional_without_claims_ok(self):
        res = build_docx.build(os.path.join(FIX, "spec.md"), None, self.tmp, provisional=True)
        self.assertTrue(res["ok"], res["findings"])
        d = docx.Document(res["outputs"][0])
        self.assertNotIn("WHAT IS CLAIMED IS:", [p.text for p in d.paragraphs])

    def test_nonprovisional_without_claims_blocks(self):
        spec = os.path.join(self.tmp, "spec.md")
        with open(os.path.join(FIX, "spec.md"), encoding="utf-8") as fh:
            txt = fh.read()
        with open(spec, "w", encoding="utf-8") as fh:
            fh.write(txt)
        res = build_docx.build(spec, None, self.tmp)
        self.assertFalse(res["ok"])
        self.assertIn("no-claims", [f["code"] for f in res["findings"] if f["level"] == "BLOCK"])

    def test_unsupported_font_rejected(self):
        with self.assertRaises(build_docx.UsageError):
            build_docx.build(os.path.join(FIX, "spec.md"), os.path.join(FIX, "claims.md"), self.tmp,
                             font="Comic Sans MS")

    def test_leftover_note_blocks_and_comment_stripped(self):
        spec = os.path.join(self.tmp, "spec.md")
        with open(os.path.join(FIX, "spec.md"), encoding="utf-8") as fh:
            txt = fh.read()
        txt = txt.replace("## BACKGROUND\n", "## BACKGROUND\n\n<!-- reviewer note: check this -->\n\n"
                                             "Bike lights exist [TODO] cite one.\n")
        with open(spec, "w", encoding="utf-8") as fh:
            fh.write(txt)
        res = build_docx.build(spec, os.path.join(FIX, "claims.md"), self.tmp)
        codes = [f["code"] for f in res["findings"]]
        self.assertIn("leftover-note", codes)
        self.assertIn("comment-stripped", codes)
        body = "\n".join(p.text for p in docx.Document(res["outputs"][0]).paragraphs)
        self.assertNotIn("reviewer note", body)

    def test_parse_claims_elements(self):
        with open(os.path.join(FIX, "claims.md"), encoding="utf-8") as fh:
            cl = build_docx.parse_claims(fh.read())
        self.assertEqual([c["num"] for c in cl], [1, 2, 3])
        self.assertEqual(len(cl[0]["elements"]), 4)
        self.assertEqual(cl[1]["elements"], [])


if __name__ == "__main__":
    unittest.main()


class SizeFeeNoteTest(unittest.TestCase):
    """F41: at 13 pages the --pdf-check message read as if a size fee applied."""

    def test_not_due(self):
        import build_docx
        self.assertEqual(build_docx.size_fee_note(13, 5),
                         "13 pages + 5 drawing sheet(s) = 18; the size fee starts above 100 sheets (spec + drawings). "
                         "Not due.")
        self.assertTrue(build_docx.size_fee_note(13).startswith(
            "13 pages; the size fee starts above 100 sheets (spec + drawings). Not due."))

    def test_may_be_due(self):
        import build_docx
        msg = build_docx.size_fee_note(120, 12)
        self.assertIn("may be due", msg)
        self.assertIn("fees.py --pages 132", msg)
