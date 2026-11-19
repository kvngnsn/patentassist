"""Offline tests for scripts/check_drawings.py (drawings <-> spec, 37 CFR 1.84 sheet checks)."""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FIX = os.path.join(HERE, "fixtures", "build")
sys.path.insert(0, SCRIPTS)

import check_drawings  # noqa: E402
import drawings  # noqa: E402

try:
    import reportlab  # noqa: F401
    HAVE_RL = True
except ImportError:
    HAVE_RL = False
try:
    import fitz  # noqa: F401
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def codes(res, level="BLOCK"):
    return [f["code"] for f in res["findings"] if f["level"] == level]


class SpecParsingTest(unittest.TestCase):
    def test_fig_refs_ranges(self):
        self.assertEqual(check_drawings.fig_refs("FIGS. 2A-2C and FIG. 4"), {"2A", "2B", "2C", "4"})
        self.assertEqual(check_drawings.fig_refs("FIGS. 5-7 show"), {"5", "6", "7"})
        self.assertEqual(check_drawings.fig_refs("FIGS. 3 and 4"), {"3", "4"})
        self.assertEqual(check_drawings.fig_refs("FIG. 10 is"), {"10"})

    def test_spec_numerals_skip_non_numerals(self):
        text = ("[0001] The battery 130 supplies about 3.7 V. Each pattern lasts 10 seconds. "
                "The array includes 12 LEDs. See claim 12 and FIG. 22. Application No. 63/123,456 "
                "filed March 3, 2026. U.S. Pat. No. 9,457,709. The shell 102 and the strap 104, 106 attach.")
        found = check_drawings.spec_numerals(text)
        self.assertEqual(sorted(found), ["102", "104", "106", "130"])
        self.assertIn("battery", found["130"][0])

    def test_figure_numerals_all_types(self):
        figs = json.loads(read(os.path.join(FIX, "figures.json")))["figures"]
        got = sorted(n for f in figs for n, _ in check_drawings.figure_numerals(f))
        self.assertIn("502", got)       # graph series
        self.assertIn("410", got)       # wireframe region
        self.assertIn("160", got)       # wireframe device + block node
        self.assertIn("302", got)       # sequence message


class CheckAgainstSpecTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pa-chk-test-")
        self.figs = os.path.join(FIX, "figures.json")
        self.spec_txt = read(os.path.join(FIX, "spec.md"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def spec(self, txt):
        p = os.path.join(self.tmp, "spec.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(txt)
        return p

    def test_clean_fixture_no_blocking(self):
        res = check_drawings.check(self.figs, os.path.join(FIX, "spec.md"))
        self.assertEqual(codes(res), [], res["findings"])
        for c in ("numerals-fig-to-spec", "numerals-spec-to-fig", "fig-brief", "fig-detailed", "numeral-unique"):
            self.assertIn(c, res["checks_run"])

    def test_numeral_missing_from_spec(self):
        txt = self.spec_txt.replace("a battery 130, ", "").replace("The battery 130 supplies about 3.7 V to the "
                                                                   "controller 110.", "")
        res = check_drawings.check(self.figs, self.spec(txt))
        bad = [f for f in res["findings"] if f["code"] == "numeral-not-in-spec"]
        self.assertEqual(len(bad), 1)
        self.assertIn("130", bad[0]["message"])
        self.assertIn("1.84(p)(5)", bad[0]["message"])

    def test_spec_numeral_missing_from_drawings(self):
        txt = self.spec_txt.replace("A mobile device 160", "A chin strap 170 holds the helmet. A mobile device 160")
        res = check_drawings.check(self.figs, self.spec(txt))
        bad = [f for f in res["findings"] if f["code"] == "numeral-not-in-drawings"]
        self.assertEqual(len(bad), 1)
        self.assertIn("170", bad[0]["message"])

    def test_fig_missing_from_brief_description(self):
        txt = self.spec_txt.replace("FIG. 3 is a sequence diagram of messages exchanged during a turn signal.\n", "")
        res = check_drawings.check(self.figs, self.spec(txt))
        self.assertIn("fig-not-in-brief", codes(res))
        self.assertIn("FIG. 3", [f["where"] for f in res["findings"] if f["code"] == "fig-not-in-brief"])

    def test_brief_lists_extra_fig(self):
        txt = self.spec_txt.replace("FIG. 2 is a flowchart", "FIG. 6 is a side view.\n\nFIG. 2 is a flowchart")
        res = check_drawings.check(self.figs, self.spec(txt))
        self.assertIn("brief-fig-missing", codes(res))

    def test_fig_not_referenced_in_detailed_description(self):
        txt = self.spec_txt.replace("FIG. 5 plots rear light output", "The controller also tracks rear light output")
        res = check_drawings.check(self.figs, self.spec(txt))
        self.assertIn("fig-not-in-detailed", codes(res))

    def test_ledger_skips_without_manifest_or_pdf(self):
        res = check_drawings.check(self.figs, os.path.join(FIX, "spec.md"))
        skipped = [s["check"] for s in res["checks_skipped"]]
        if not os.path.exists(os.path.join(FIX, "out", "drawings-manifest.json")):
            self.assertIn("manifest-fresh", skipped)
            self.assertIn("pdf-margins", skipped)
            self.assertFalse(res["summary"]["complete"])


@unittest.skipUnless(HAVE_RL and HAVE_FITZ, "reportlab and PyMuPDF needed")
class CheckSheetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="pa-chk-test-")
        cls.out = os.path.join(cls.tmp, "out")
        cls.build = drawings.build(os.path.join(FIX, "figures.json"), cls.out, d=None, no_audit=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_built_sheets_pass_every_check(self):
        res = check_drawings.check(os.path.join(FIX, "figures.json"), os.path.join(FIX, "spec.md"),
                                   self.build["manifest"])
        self.assertEqual(codes(res), [], res["findings"])
        self.assertEqual(res["checks_skipped"], [])
        for c in ("pdf-page-size", "pdf-margins", "pdf-text-height", "pdf-black-only", "pdf-fonts-embedded",
                  "pdf-sheet-numbers", "pdf-fig-labels", "manifest-fresh", "manifest-numerals"):
            self.assertIn(c, res["checks_run"])

    def test_stale_manifest(self):
        data = json.loads(read(os.path.join(FIX, "figures.json")))
        data["figures"][3]["regions"][0]["numeral"] = 412
        p = os.path.join(self.tmp, "figures-edited.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        res = check_drawings.check(p, os.path.join(FIX, "spec.md"), self.build["manifest"])
        self.assertIn("drawings-stale", codes(res))
        self.assertIn("built-numerals-differ", codes(res))

    def test_bad_pdf_color_small_text_margin_font(self):
        from reportlab.pdfgen import canvas
        bad = os.path.join(self.tmp, "bad.pdf")
        c = canvas.Canvas(bad, pagesize=(612, 792))
        c.setStrokeColorRGB(1, 0, 0)
        c.line(100, 400, 300, 400)                 # red line
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 8)                  # 8 pt Helvetica: cap height 0.20 cm, not embedded
        c.drawString(150, 300, "102")
        c.setFont("Helvetica", 14)
        c.drawString(5, 780, "MARGIN")             # inside the top/left margin
        c.showPage()
        c.save()
        res = check_drawings.check(os.path.join(FIX, "figures.json"), os.path.join(FIX, "spec.md"),
                                   self.build["manifest"], bad)
        got = codes(res)
        for code in ("not-black", "text-too-small", "outside-sight", "font-not-embedded"):
            self.assertIn(code, got)
        self.assertIn("sheet-number", codes(res, "WARN"))

    def test_page_size_rule(self):
        from reportlab.pdfgen import canvas
        bad = os.path.join(self.tmp, "legal.pdf")
        c = canvas.Canvas(bad, pagesize=(612, 1008))
        c.showPage()
        c.save()
        res = check_drawings.check(os.path.join(FIX, "figures.json"), os.path.join(FIX, "spec.md"),
                                   self.build["manifest"], bad)
        self.assertIn("page-size", codes(res))


if __name__ == "__main__":
    unittest.main()


class TestDogfoodSpecParsing(unittest.TestCase):
    """Found dogfooding a historical synthetic drafting exercise: '###' sub-headings inside the Detailed Description hid
    every FIG. reference, and '14 of the 16 trials' was read as numerals 14 and 16 (both BLOCK)."""

    def test_subheadings_stay_in_detailed_description(self):
        md = "## DETAILED DESCRIPTION\n\nIntro.\n\n### Overview\n\nReferring to FIG. 1, a pad 120.\n\n## ABSTRACT\n\nX.\n"
        secs = check_drawings.split_sections(md)
        self.assertIn("FIG. 1", check_drawings.find_section(secs, "DETAILED DESCRIPTION"))

    def test_counts_are_not_numerals(self):
        found = check_drawings.spec_numerals("The signature was detected before 14 of the 16 boil-overs by a pad 120.")
        self.assertEqual(sorted(found), ["120"])
