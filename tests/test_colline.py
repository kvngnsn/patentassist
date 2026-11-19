"""Offline tests for colline.py (column:line pinpoints from grant PDFs).

Fixtures in tests/fixtures/colline/ are the real Google Patents grant PDFs (image + OCR text layer):
  US9457709B2.pdf  2016 grant, 17 pages: front page, drawing sheets 2-11, spec + claims pages 12-17
  US5560126A.pdf   1996 grant, 30 pages: front page, drawing sheets 2-21, spec + claims pages 22-30
Every expected pinpoint below was checked by eye against the page rendered to PNG.
"""

import contextlib
import gzip
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

try:
    import fitz  # noqa: F401
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False

import colline  # noqa: E402
from patent_fetch import parse_google_html  # noqa: E402
from state import SCHEMA_CHART, empty_prior_art, read_json, write_json  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "colline")
NEW = os.path.join(FIX, "US9457709B2.pdf")
OLD = os.path.join(FIX, "US5560126A.pdf")
HTML = os.path.join(HERE, "fixtures", "search", "US9457709B2.html")
WIDENED = "note: range widened by one line (text sits between gutter line positions)"


def google_record():
    with open(HTML, encoding="utf-8") as fh:
        return parse_google_html(fh.read(), requested="US9457709B2")


@unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
class TestLayout(unittest.TestCase):
    def test_new_grant_spec_pages_and_columns(self):
        lay = colline.get_layout(NEW)
        self.assertEqual(lay["problems"], [])
        sp = lay["spec_pages"]
        self.assertEqual([p["page"] for p in sp], [12, 13, 14, 15, 16, 17])  # front page + drawings skipped
        self.assertEqual([p["columns"] for p in sp], [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]])
        self.assertTrue(all(p["columns_source"] == "printed" for p in sp))
        self.assertTrue(all(p["layout"] == "gutter" and p["markers"] >= 3 for p in sp))
        self.assertAlmostEqual(sp[0]["pitch"], 9.985, places=2)

    def test_old_grant_spec_pages_and_columns(self):
        lay = colline.get_layout(OLD)
        sp = lay["spec_pages"]
        self.assertEqual([p["page"] for p in sp], list(range(22, 31)))
        self.assertEqual(sp[0]["columns"], [1, 2])
        self.assertEqual(sp[-1]["columns"], [17, 18])
        # page 24's left numeral is not in the OCR layer; the page sequence still confirms it
        self.assertEqual(sp[2]["printed_numerals"], [None, 6])
        self.assertEqual(sp[2]["columns"], [5, 6])

    def test_image_only_pdf_is_not_guessed(self):
        import fitz
        d = tempfile.mkdtemp()
        try:
            src, out = fitz.open(NEW), fitz.open()
            for i in (0, 11, 12):
                pg = out.new_page(width=src[i].rect.width, height=src[i].rect.height)
                pg.insert_image(pg.rect, pixmap=src[i].get_pixmap(dpi=50))
            path = os.path.join(d, "img.pdf")
            out.save(path)
            r = colline.locate(path, "methodology for activating turn signals in a head protection")
            self.assertFalse(r["found"])
            self.assertIsNone(r["pinpoint"])
            self.assertIsNone(r["confidence"])
            self.assertIn("no text layer", r["reason"])
        finally:
            shutil.rmtree(d)


@unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
class TestLocateNewGrant(unittest.TestCase):
    def check(self, quote, pin, page, conf="high", end_page=None, context=None):
        r = colline.locate(NEW, quote, context=context)
        self.assertTrue(r["found"], r)
        self.assertEqual(r["pinpoint"], pin, r)
        self.assertEqual(r["page"], page)
        self.assertEqual(r["confidence"], conf, r["reasons"])
        if end_page:
            self.assertEqual(r["end_page"], end_page)
        return r

    def test_single_line(self):
        r = self.check("methodology for activating turn signals in a head protection", "col. 2, l. 20", 12)
        self.assertEqual(r["score"], 1.0)
        self.assertEqual(r["matched_text"], "methodology for activating turn signals in a head protection")
        self.assertEqual(r["start"], {"page": 12, "column": 2, "line": 20})

    def test_spans_column_break(self):
        self.check("FIG. 5 is a schematic of a helmet with an adaptive light notification system according to one "
                   "example; FIG. 6A illustrates a side view of a helmet", "col. 1, l. 66 – col. 2, l. 1", 12)

    def test_spans_page_break(self):
        r = self.check("When the turn signals 102, 104 and the backlight 106 are removably attached",
                       "col. 2, l. 67 – col. 3, l. 1", 12, end_page=13)
        self.assertIn("106 are removably attached", r["matched_text"])

    def test_claim_text_and_repeats(self):
        q = "wherein the sensor is a proximity sensor, a positive sensitive device or a capacitive touch detector"
        rec = google_record()
        claim12 = [c["text"] for c in rec["claims"] if c["num"] == 12][0]
        claim20 = [c["text"] for c in rec["claims"] if c["num"] == 20][0]
        r = self.check(q, "col. 10, ll. 58-60", 16, context=claim12)  # claim 12, checked on the page
        self.assertEqual(r["also"], ["col. 12, ll. 28-31"])
        r = colline.locate(NEW, q, context=claim20)  # same words in claim 20 on the last page
        self.assertTrue(r["pinpoint"].startswith("col. 12, ll. 28"))

    def test_line_between_grid_positions_widens(self):
        # col. 5 text drifts against the gutter grid (marker 35 prints between two lines); the
        # last line sits halfway between positions 32 and 33, so the range covers both.
        r = self.check("In selected embodiments, the first microcontroller 202 may also check whether the bicycle "
                       "is idle", "col. 5, ll. 31-33", 14)
        self.assertIn(WIDENED, r["reasons"])

    def test_hyphenation_ligatures_and_quote_marks(self):
        # printed "illumi-/nation" (the OCR layer drops the hyphen) and "pur-/pose"; curly quotes
        r = self.check("safe especially under circumstances of poor ambient illumination",
                       "col. 1, ll. 23-24", 12)
        self.assertIn("illumi", r["matched_text"])
        r = colline.locate(NEW, "The foregoing “background” description is for the purpose of generally")
        self.assertTrue(r["found"])
        self.assertEqual(r["start"]["column"], 1)

    def test_ellipsis(self):
        r = colline.locate(NEW, "Safety is an important concern ... clearly communicating a cyclist")
        self.assertTrue(r["found"])
        self.assertTrue(r["pinpoint"].startswith("col. 1, ll. 15-"))

    def test_ocr_noise_tolerated(self):
        r = colline.locate(NEW, "Safetv is an imp0rtant concem for most cvclists and bikers. 0ften cyclists and "
                                "drivers share the same route")
        self.assertTrue(r["found"])
        self.assertTrue(r["pinpoint"].startswith("col. 1, ll. 15-"))
        self.assertLess(r["score"], 1.0)
        self.assertGreaterEqual(r["score"], colline.HIGH_SCORE)

    def test_heavy_noise_is_low_confidence(self):
        r = colline.locate(NEW, "It is ofter desireable for cvclist to indicale there futur directon for motorist. "
                                "Cyclist oftem uses hamd signal to indicale thier intentoins to othr trafic.")
        self.assertTrue(r["found"])
        self.assertEqual(r["confidence"], "low")
        self.assertEqual(r["start"]["column"], 2)
        self.assertTrue(any("fuzzy match" in x for x in r["reasons"]))

    def test_not_found_and_too_short(self):
        r = colline.locate(NEW, "The quick brown fox jumps over the lazy dog while the helmet sleeps")
        self.assertFalse(r["found"])
        self.assertIsNone(r["pinpoint"])
        self.assertIn("closest", r)
        r = colline.locate(NEW, "turn signal")
        self.assertFalse(r["found"])
        self.assertIn("too short", r["reason"])


@unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
class TestLocateOldGrant(unittest.TestCase):
    def check(self, quote, pin, page):
        r = colline.locate(OLD, quote)
        self.assertTrue(r["found"], r)
        self.assertEqual(r["pinpoint"], pin, r)
        self.assertEqual(r["page"], page)
        self.assertEqual(r["confidence"], "high", r["reasons"])
        return r

    def test_known_lines(self):
        self.check("or a rubber compound. When laminated, the sole is attached", "col. 1, l. 20", 22)
        self.check("FIG. 10 is an exploded isometric view of a heel support and rear sole for the shoe of FIG. 9.",
                   "col. 4, ll. 3-4", 23)
        self.check("The rear sole 28 is detachable from the heel support 26. This allows the user the ability to "
                   "change rear soles entirely when either the sole is worn to a significant degree",
                   "col. 5, ll. 42-44", 24)

    def test_column_break_and_claims(self):
        self.check("able, full-length sole for every men's and women's shoe size is to be produced",
                   "col. 1, l. 67 – col. 2, l. 1", 22)
        self.check("42. The shoe of claim 41, wherein the rear sole includes a plurality of beveled segments "
                   "separated from each other by the substantially planar portion of the bottom surface.",
                   "col. 18, ll. 17-19", 30)

    def test_half_line_paragraph_offset_widens(self):
        # 1990s typesetting: after a paragraph gap the right column sits half a line off the gutter
        # numbers ("Shoes with ..." is between positions 19 and 20, "screw or ..." between 20 and 21).
        r = self.check("Shoes with detachable rear soles that incorporate a center screw", "col. 2, ll. 19-21", 22)
        self.assertIn(WIDENED, r["reasons"])


class Matter(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "cache"))

    def tearDown(self):
        shutil.rmtree(self.d)

    def add_record(self, drop_pdf_url=False, raw_html=False):
        rec = google_record()
        if drop_pdf_url:
            rec["pdf_url"] = None
        write_json(os.path.join(self.d, "cache", "US9457709B2.json"), rec)
        if raw_html:
            raw = os.path.join(self.d, "cache", "raw", "google_patents")
            os.makedirs(raw, exist_ok=True)
            with open(HTML, "rb") as src, gzip.open(os.path.join(raw, "US9457709B2.html.gz"), "wb") as dst:
                dst.write(src.read())
        return rec

    def add_pdf(self, src=NEW, name="US9457709B2"):
        os.makedirs(colline.pdf_dir(self.d), exist_ok=True)
        shutil.copyfile(src, os.path.join(colline.pdf_dir(self.d), name + ".pdf"))

    def audit_lines(self):
        p = os.path.join(self.d, "audit.jsonl")
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as fh:
            return [json.loads(x) for x in fh if x.strip()]


class TestFetchOffline(Matter):
    URL = "https://patentimages.storage.googleapis.com/f3/54/6e/2ce70d0b1b121e/US9457709.pdf"

    def test_pdf_url_from_record_html_and_missing(self):
        with open(HTML, encoding="utf-8") as fh:
            self.assertEqual(colline.pdf_url_from_html(fh.read()), self.URL)
        self.add_record()
        self.assertEqual(colline.pdf_url_for(self.d, "US9457709B2", offline=True)[0], self.URL)
        self.add_record(drop_pdf_url=True, raw_html=True)
        url, num, how = colline.pdf_url_for(self.d, "9457709", offline=True)
        self.assertEqual((url, num, how), (self.URL, "US9457709B2", "cached Google Patents HTML"))
        os.remove(os.path.join(self.d, "cache", "raw", "google_patents", "US9457709B2.html.gz"))
        self.assertIsNone(colline.pdf_url_for(self.d, "US9457709B2", offline=True)[0])

    def test_import_local_file_and_cache_lookup(self):
        res = colline.run({"command": "fetch", "numbers": ["5,560,126"], "file": OLD, "dir": self.d})
        self.assertEqual(res["exit_code"], 0, res)
        self.assertEqual(res["results"][0]["status"], "imported")
        self.assertTrue(os.path.exists(os.path.join(self.d, "cache", "pdf", "US5560126A.pdf")))
        self.assertEqual(colline.find_pdf(self.d, "US5560126"), os.path.join(self.d, "cache", "pdf", "US5560126A.pdf"))
        res = colline.run({"command": "fetch", "numbers": ["US5560126A"], "dir": self.d, "offline": True})
        self.assertEqual(res["results"][0]["status"], "cached")
        a = self.audit_lines()
        self.assertEqual(a[0]["kind"], "fetch")
        self.assertEqual(a[0]["source"], "local_file")

    def test_offline_not_cached_and_bad_input(self):
        res = colline.run({"command": "fetch", "numbers": ["US9457709B2"], "dir": self.d, "offline": True,
                           "no_audit": True})
        self.assertEqual(res["exit_code"], 3)
        self.assertEqual(res["results"][0]["status"], "not_cached")
        with self.assertRaises(colline.UsageError):
            colline.run({"command": "fetch", "numbers": ["US20160144773A1"], "dir": self.d})

    def test_refuses_pdf_link_on_other_host(self):
        rec = self.add_record()
        rec["pdf_url"] = "https://example.com/US9457709.pdf"
        write_json(os.path.join(self.d, "cache", "US9457709B2.json"), rec)
        r = colline.fetch_pdf(self.d, "US9457709B2", no_audit=True)  # refused before any request
        self.assertEqual(r["status"], "not_found")
        self.assertIn("refusing", r["message"])

    @unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
    def test_locate_in_cache_never_fetches(self):
        r = colline.locate_in_cache(self.d, "US9457709B2", "methodology for activating turn signals")
        self.assertFalse(r["found"])
        self.assertIn("not cached", r["reason"])
        self.add_pdf()
        r = colline.locate_in_cache(self.d, "9457709", "methodology for activating turn signals in a head")
        self.assertEqual(r["pinpoint"], "col. 2, l. 20")


@unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
class TestAnnotate(Matter):
    Q_SINGLE = "methodology for activating turn signals in a head protection"
    Q_SPAN = ("FIG. 5 is a schematic of a helmet with an adaptive light notification system according to one "
              "example; FIG. 6A illustrates a side view of a helmet")

    def build(self, with_pdf=True):
        self.add_record()
        if with_pdf:
            self.add_pdf()
        pa = empty_prior_art()
        pa["references"] = [
            {"id": "R1", "type": "patent", "number": "US9457709B2", "element_map": {
                "E1": {"state": "explicit", "pinpoint": "p17", "quote": self.Q_SINGLE},
                "E2": {"state": "explicit", "pinpoint": "claim 3", "quote": self.Q_SINGLE},
                "E3": {"state": "absent", "pinpoint": None, "quote": None},
                "E4": {"state": "partial", "pinpoint": None,
                       "quote": "It is ofter desireable for cvclist to indicale there futur directon for motorist. "
                                "Cyclist oftem uses hamd signal to indicale thier intentoins to othr trafic."},
                "E5": {"state": "explicit", "pinpoint": "p3", "quote": "an entirely invented sentence about "
                                                                       "submarine periscopes and lighthouses",
                       "pinpoint_colline": "col. 9, l. 1"}}},
            {"id": "R2", "type": "application", "number": "US20160144773A1", "element_map": {
                "E1": {"state": "explicit", "pinpoint": "[0018]", "quote": self.Q_SINGLE}}},
        ]
        write_json(os.path.join(self.d, "prior-art.json"), pa)
        chart = {"schema": SCHEMA_CHART, "kind": "patentability", "elements": [{"id": "1a", "text": "x"}],
                 "refs": [{"id": "R1", "number": "US9457709B2"}],
                 "cells": [{"element": "1a", "ref": "R1", "state": "explicit", "quote": self.Q_SPAN,
                            "pinpoint": None, "verified": False}]}
        write_json(os.path.join(self.d, "charts", "r1.json"), chart)

    def test_prior_art_fill_keeps_pinpoint(self):
        self.build()
        res = colline.run({"command": "annotate", "dir": self.d, "from_file": os.path.join(self.d, "prior-art.json")})
        self.assertEqual(res["exit_code"], 0, res)
        em = read_json(os.path.join(self.d, "prior-art.json"))["references"][0]["element_map"]
        self.assertEqual(em["E1"]["pinpoint"], "p17")  # untouched
        self.assertEqual(em["E1"]["pinpoint_colline"], "col. 2, l. 20")
        self.assertNotIn("pinpoint_colline", em["E2"])  # claim pinpoints are already printed
        self.assertNotIn("pinpoint_colline", em["E4"])  # low confidence: candidate only
        self.assertEqual(em["E4"]["pinpoint_colline_candidate"][:6], "col. 2")
        self.assertNotIn("pinpoint_colline", em["E5"])  # stale value removed when the quote is not found
        r2 = read_json(os.path.join(self.d, "prior-art.json"))["references"][1]["element_map"]["E1"]
        self.assertNotIn("pinpoint_colline", r2)  # application: printed paragraph numbers
        s = res["summary"]
        self.assertEqual((s["candidates"], s["filled"], s["low"], s["not_found"]), (3, 1, 1, 1))
        self.assertEqual(s["skipped"], 2)
        codes = [f["code"] for f in res["findings"]]
        self.assertIn("colline_low_confidence", codes)
        self.assertIn("colline_not_found", codes)
        self.assertIn("colline_removed", codes)
        quotes = [x for x in self.audit_lines() if x["kind"] == "quote" and x.get("result") == "colline"]
        self.assertEqual(len(quotes), 3)
        self.assertEqual(quotes[0]["pinpoint_colline"], "col. 2, l. 20")

    def test_chart_cells_and_dry_run(self):
        self.build()
        path = os.path.join(self.d, "charts", "r1.json")
        before = read_json(path)
        res = colline.run({"command": "annotate", "dir": self.d, "chart": "charts/r1.json", "dry_run": True,
                           "no_audit": True})
        self.assertEqual(res["summary"]["filled"], 1)
        self.assertEqual(read_json(path), before)
        colline.run({"command": "annotate", "dir": self.d, "chart": path, "no_audit": True})
        cell = read_json(path)["cells"][0]
        self.assertIsNone(cell["pinpoint"])
        self.assertEqual(cell["pinpoint_colline"], "col. 1, l. 66 – col. 2, l. 1")

    def test_offline_without_pdf_warns(self):
        self.build(with_pdf=False)
        res = colline.run({"command": "annotate", "dir": self.d, "chart": "charts/r1.json", "offline": True,
                           "no_audit": True})
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("pdf_unavailable", [f["code"] for f in res["findings"]])
        self.assertNotIn("pinpoint_colline", read_json(os.path.join(self.d, "charts", "r1.json"))["cells"][0])


@unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
class TestCli(Matter):
    def test_locate_json(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = colline.main(["locate", "--pdf", OLD, "or a rubber compound. When laminated, the sole is attached",
                                 "--dir", self.d, "--json", "--no-audit"])
        self.assertEqual(code, 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["pinpoint"], "col. 1, l. 20")
        self.assertEqual(data["page"], 22)
        self.assertEqual(data["confidence"], "high")

    def test_locate_not_found_exit_1(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = colline.main(["locate", "--pdf", NEW, "an entirely invented sentence about submarine periscopes",
                                 "--dir", self.d, "--no-audit"])
        self.assertEqual(code, 1)
        self.assertIn("colline_not_found", out.getvalue())

    def test_layout_text(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = colline.main(["layout", "--pdf", NEW, "--dir", self.d, "--no-audit"])
        self.assertEqual(code, 0)
        self.assertIn("6 specification pages", out.getvalue())


if __name__ == "__main__":
    unittest.main()
