"""Offline tests for verify_refs.py, quote_check.py, search_log.py, ids.py (cache built from fixtures)."""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import ids  # noqa: E402
import quote_check  # noqa: E402
import search_log  # noqa: E402
import verify_refs  # noqa: E402
from patent_fetch import parse_google_html  # noqa: E402
from state import empty_prior_art, read_json, write_json  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "search")


def make_matter(refs, cutoff="2016-08-01", charts=None, elements=None):
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "cache"))
    for n in ("US9457709B2", "US20160144773A1", "EP1000000B1"):
        with open(os.path.join(FIX, n + ".html"), encoding="utf-8") as fh:
            write_json(os.path.join(d, "cache", n + ".json"), parse_google_html(fh.read(), requested=n))
    pa = empty_prior_art()
    pa["cutoff_date"] = cutoff
    pa["references"] = refs
    if elements:
        pa["elements"] = elements
    write_json(os.path.join(d, "prior-art.json"), pa)
    for name, chart in (charts or {}).items():
        write_json(os.path.join(d, "charts", name), chart)
    return d


def codes(res, level=None):
    return [f["code"] for f in res["findings"] if level is None or f["level"] == level]


class Base(unittest.TestCase):
    def tearDown(self):
        if getattr(self, "d", None):
            shutil.rmtree(self.d)


class TestVerify(Base):
    def run_verify(self, refs, **kw):
        self.d = make_matter(refs, **kw)
        res = verify_refs.run({"dir": self.d, "offline": True, "no_audit": True, "today": "2026-11-18"})
        return res, read_json(os.path.join(self.d, "prior-art.json"))

    def test_good_reference_verified_and_filled(self):
        res, pa = self.run_verify([{"id": "R1", "type": "patent", "number": "US9457709B2",
                                    "title": "Bicycle helmet with an adaptive light notification system that varies brightness",
                                    "assignee_or_authors": "Reem Jafar Alataas", "grant_date": "2016-10-04"}])
        self.assertEqual(res["exit_code"], 0, res["findings"])
        r = pa["references"][0]
        self.assertTrue(r["verified"])
        self.assertIn("title", r["verified_how"])
        self.assertIn("single source", r["verified_how"])
        self.assertEqual(r["verified_on"], "2026-11-18")
        self.assertEqual(r["priority_date"], "2014-11-26")
        self.assertEqual(r["pub_date"], "2016-05-26")  # earliest publication of the application (the A1)

    def test_title_mismatch_blocks(self):
        res, pa = self.run_verify([{"id": "R1", "type": "patent", "number": "EP1000000B1",
                                    "title": "Helmet with turn signal lights"}])
        self.assertEqual(res["exit_code"], 1)
        self.assertIn("title_mismatch", codes(res, "BLOCK"))
        self.assertFalse(pa["references"][0]["verified"])

    def test_kind_date_assignee_mismatch_blocks(self):
        res, pa = self.run_verify([
            {"id": "R1", "type": "patent", "number": "US9457709B1"},
            {"id": "R2", "type": "patent", "number": "EP1000000B1", "grant_date": "2004-01-01"},
            {"id": "R3", "type": "application", "number": "US20160144773A1", "assignee_or_authors": "Apple Inc."},
        ], cutoff="2026-01-01")
        bl = codes(res, "BLOCK")
        self.assertIn("kind_mismatch", bl)
        self.assertIn("date_mismatch", bl)
        self.assertIn("assignee_mismatch", bl)

    def test_unfetchable_is_warn_not_block(self):
        res, pa = self.run_verify([{"id": "R1", "type": "patent", "number": "US8000001B2"}])
        self.assertIn("unverified", codes(res, "WARN"))
        self.assertNotIn("unverified", codes(res, "BLOCK"))
        self.assertFalse(pa["references"][0]["verified"])

    def test_family_merge_pub_and_grant(self):
        res, pa = self.run_verify([
            {"id": "R1", "type": "application", "number": "US 2016/0144773 A1",
             "element_map": {"E1": {"state": "explicit", "quote": "head protection enclosure", "pinpoint": None}}},
            {"id": "R2", "type": "patent", "number": "9457709"},
            {"id": "R3", "type": "patent", "number": "EP1000000B1"},
        ])
        refs = pa["references"]
        self.assertEqual(len(refs), 2)
        r1 = refs[0]
        self.assertEqual(r1["id"], "R1")
        self.assertEqual(r1["number"], "US9457709B2")           # the grant is the primary document
        self.assertEqual(r1["family"], ["US20160144773A1"])
        self.assertEqual(r1["merged_from"], ["R2"])
        self.assertEqual(r1["pub_date"], "2016-05-26")
        self.assertEqual(r1["element_map"]["E1"]["source_number"], "US20160144773A1")
        self.assertIn("family_merge", codes(res, "INFO"))

    def test_prior_art_basis_102a1_and_not_prior_art(self):
        res, pa = self.run_verify([{"id": "R1", "type": "patent", "number": "EP1000000B1"}], cutoff="2010-01-01")
        self.assertEqual(pa["references"][0]["prior_art_basis"], "102(a)(1)")
        res, pa = self.run_verify([{"id": "R1", "type": "patent", "number": "EP1000000B1"}], cutoff="1999-01-01")
        self.assertEqual(pa["references"][0]["prior_art_basis"], "not_prior_art")

    def test_prior_art_basis_102a2_for_us_earlier_filed_later_published(self):
        # US20160144773A1: filed 2014-11-26, published 2016-05-26. Cutoff between those dates.
        res, pa = self.run_verify([{"id": "R1", "type": "application", "number": "US20160144773A1"}],
                                  cutoff="2015-06-01")
        self.assertEqual(pa["references"][0]["prior_art_basis"], "102(a)(2)")
        # EP document filed before but published after: NOT 102(a)(2) (not US / WO).
        res, pa = self.run_verify([{"id": "R1", "type": "patent", "number": "EP1000000B1"}], cutoff="1999-12-01")
        self.assertEqual(pa["references"][0]["prior_art_basis"], "not_prior_art")

    def test_basis_function_wo_and_web(self):
        cb = verify_refs.compute_basis
        self.assertEqual(cb({"number": "WO2019123456A1", "type": "application", "pub_date": "2019-06-27",
                             "priority_date": "2017-12-20"}, "2018-06-01")[0], "102(a)(2)")
        self.assertEqual(cb({"type": "web", "url": "http://x.example"}, "2018-06-01")[0], "needs_evidence")
        self.assertEqual(cb({"type": "npl", "pub_date": "2018"}, "2018-06-01")[0], "needs_evidence")
        self.assertEqual(cb({"type": "npl", "pub_date": "2017"}, "2018-06-01")[0], "102(a)(1)")

    def test_name_match(self):
        self.assertTrue(verify_refs.name_match("Raytheon Company", ["Raytheon Co"]))
        self.assertTrue(verify_refs.name_match("Alataas", ["Reem Jafar ALATAAS"]))
        self.assertFalse(verify_refs.name_match("Apple Inc.", ["Raytheon Co", "Joseph Marron"]))


class TestQuoteCheck(Base):
    def test_pass_fail_and_pinpoints(self):
        refs = [{"id": "R1", "type": "application", "number": "US20160144773A1", "element_map": {
            "E1": {"state": "explicit", "pinpoint": None,
                   "quote": "The present disclosure relates to an adaptive light notification system comprising a "
                            "head protection enclosure"},
            "E2": {"state": "explicit", "pinpoint": "[0099]",
                   "quote": "The turn signals are included in the adaptive light notification system to increase visibility"},
            "E3": {"state": "partial", "pinpoint": None,
                   "quote": "THE FOREGOING “BACKGROUND” DESCRIPTION is for the purpose of generally "
                            "presenting … the context of the disclosure"},
            "E4": {"state": "absent", "pinpoint": None, "quote": None},
        }}]
        self.d = make_matter(refs)
        res = quote_check.run({"dir": self.d, "no_audit": True})
        self.assertEqual(res["exit_code"], 1)
        nf = [f for f in res["findings"] if f["code"] == "quote_not_found"]
        self.assertEqual(len(nf), 1)
        self.assertIn("R1.E2", nf[0]["where"])
        self.assertIn("to serve as", nf[0]["message"])     # closest real wording is suggested
        self.assertIn("[0019]", nf[0]["message"])
        em = read_json(os.path.join(self.d, "prior-art.json"))["references"][0]["element_map"]
        self.assertEqual(em["E1"]["pinpoint"], "[0004]")
        self.assertEqual(em["E3"]["pinpoint"], "[0003]")
        # quote text is never altered
        self.assertEqual(em["E2"]["quote"], refs[0]["element_map"]["E2"]["quote"])
        self.assertEqual(em["E2"]["pinpoint"], "[0099]")

    def test_claim_pinpoint_and_chart(self):
        chart = {"schema": "patentassist/chart@1", "kind": "patentability", "subject": {"type": "invention"},
                 "elements": [{"id": "1a", "text": "x"}], "refs": [{"id": "R1", "number": "EP1000000B1"}],
                 "cells": [{"element": "1a", "ref": "R1", "state": "explicit", "verified": False,
                            "quote": "characterized in that the apparatus further comprises a frame (26) with stop members (27)",
                            "pinpoint": None}]}
        self.d = make_matter([], charts={"c1.json": chart})
        res = quote_check.run({"dir": self.d, "no_audit": True})
        self.assertEqual(res["exit_code"], 0, res["findings"])
        cell = read_json(os.path.join(self.d, "charts", "c1.json"))["cells"][0]
        self.assertEqual(cell["pinpoint"], "claim 1")
        self.assertFalse(cell["verified"])  # human tick is untouched

    def test_missing_cache_blocks(self):
        refs = [{"id": "R1", "type": "patent", "number": "US8000001B2",
                 "element_map": {"E1": {"state": "explicit", "quote": "anything", "pinpoint": None}}}]
        self.d = make_matter(refs)
        res = quote_check.run({"dir": self.d, "no_audit": True})
        self.assertIn("no_cache", codes(res, "BLOCK"))

    def test_normalization(self):
        n = quote_check.norm
        self.assertEqual(n("A—B “C”  d"), n('a-b "c" D'))
        self.assertEqual(n("sensors 204 , 206"), n("sensors 204, 206"))


class TestSearchLogAndIds(Base):
    def test_log_coverage_diff(self):
        self.d = make_matter([], elements=[{"id": "E1", "text": "shell", "essential": True},
                                           {"id": "E2", "text": "light", "essential": True},
                                           {"id": "E3", "text": "radio", "essential": True}])
        base = {"dir": self.d, "no_audit": True}
        search_log.run(dict(base, command="add", source="google_patents_web", query="helmet light", hits=10,
                            screened=8, elements="E1,E2", results="US9457709B2,US 2016/0144773 A1", date="2026-11-01"))
        search_log.run(dict(base, command="add", source="websearch", query="helmet light product", hits=4,
                            elements="E2", date="2026-11-02"))
        pa = read_json(os.path.join(self.d, "prior-art.json"))
        self.assertEqual([q["id"] for q in pa["queries"]], ["Q1", "Q2"])
        self.assertEqual(pa["queries"][0]["results"], ["US9457709B2", "US20160144773A1"])
        cov = search_log.run(dict(base, command="coverage"))
        self.assertEqual(cov["coverage"]["never_searched"], ["E3"])
        self.assertIn("never_searched", codes(cov, "WARN"))
        plan = search_log.run(dict(base, command="rerun-plan", since="2026-11-10"))
        self.assertEqual([p["rerun_of"] for p in plan["plan"]], ["Q1", "Q2"])
        r = search_log.run(dict(base, command="add", source="google_patents_web", query="helmet light", hits=12,
                                results="US9457709B2,US10011216B1,US20160144773A1", date="2026-11-18"))
        self.assertEqual(r["query"]["rerun_of"], "Q1")
        diff = search_log.run(dict(base, command="diff", since="2026-11-10"))
        self.assertEqual(diff["new_numbers"], ["US10011216B1"])
        plan2 = search_log.run(dict(base, command="rerun-plan", since="2026-11-10"))
        self.assertEqual([p["rerun_of"] for p in plan2["plan"]], ["Q2"])

    def test_ids_sections_and_exclusion(self):
        refs = [
            {"id": "R1", "type": "patent", "number": "US9457709B2", "verified": True, "family": ["US20160144773A1"],
             "prior_art_basis": "102(a)(1)"},
            {"id": "R2", "type": "patent", "number": "EP1000000B1", "verified": True, "prior_art_basis": "102(a)(1)"},
            {"id": "R3", "type": "npl", "verified": True, "title": "Integrated Helmet System",
             "assignee_or_authors": "Allen Thomas", "pub_date": "2008-05-02", "url": "http://example.edu/x.pdf"},
            {"id": "R4", "type": "patent", "number": "US8000001B2", "verified": False},
        ]
        self.d = make_matter(refs)
        res = ids.run({"dir": self.d, "no_audit": True, "include_family": True})
        self.assertEqual(res["exit_code"], 0, res["findings"])
        doc = read_json(os.path.join(self.d, "draft", "out", "ids.json"))
        s = doc["sections"]
        self.assertEqual(s["us_patents"][0]["document_number"], "US-9,457,709-B2")
        self.assertEqual(s["us_patents"][0]["issue_date"], "2016-10-04")
        self.assertEqual(s["us_patents"][0]["patentee"], "Reem Jafar ALATAAS")
        self.assertEqual(s["us_publications"][0]["document_number"], "US-20160144773-A1")
        self.assertEqual(s["us_publications"][0]["publication_date"], "2016-05-26")
        self.assertEqual(s["foreign"][0]["country"], "EP")
        self.assertEqual(s["foreign"][0]["applicant"], "Beheermaatschappij De Boer Nijmegen BV")
        self.assertIsNone(s["foreign"][0]["non_english"])
        self.assertFalse(s["foreign"][0]["translation_attached"])
        self.assertNotIn("relevance_statement", s["foreign"][0])
        self.assertIn("Integrated Helmet System", s["npl"][0]["citation"])
        self.assertEqual([e["ref"] for e in doc["excluded"]], ["R4"])
        self.assertEqual(doc["count"], 4)
        self.assertEqual(doc["size_fee_tier"], 0)
        with open(os.path.join(self.d, "draft", "out", "ids.csv"), encoding="utf-8") as fh:
            self.assertEqual(len(fh.read().strip().splitlines()), 5)

    def test_ids_non_english_columns(self):
        """F28: non_english is not the SB/08 T box; translation_attached defaults false; non-English
        documents get a relevance_statement (stub or given) for 37 CFR 1.98(a)(3)(i)."""
        refs = [
            {"id": "R1", "type": "patent", "number": "DE3146638A1", "verified": True},
            {"id": "R2", "type": "patent", "number": "EP1000000B1", "verified": True,
             "translation_attached": True, "relevance_statement": "Shows a frame with stop members (claim 1)."},
            {"id": "R3", "type": "patent", "number": "GB2000000A", "verified": True},
        ]
        self.d = make_matter(refs)
        write_json(os.path.join(self.d, "cache", "DE3146638A1.json"),
                   {"schema": "patentassist/patent@1", "number": "DE3146638A1", "country": "DE",
                    "publication_date": "1983-06-01", "inventors": ["Hans Muster"], "notes": []})
        write_json(os.path.join(self.d, "cache", "GB2000000A.json"),
                   {"schema": "patentassist/patent@1", "number": "GB2000000A", "country": "GB",
                    "publication_date": "1979-01-01", "inventors": ["Jo Bloggs"], "notes": []})
        p = os.path.join(self.d, "cache", "EP1000000B1.json")
        rec = read_json(p)
        rec["notes"].append("Text is Google machine translation from Dutch; quote it as machine-translated.")
        write_json(p, rec)
        res = ids.run({"dir": self.d, "no_audit": True})
        f = {r["ref"]: r for r in read_json(os.path.join(self.d, "draft", "out", "ids.json"))["sections"]["foreign"]}
        self.assertEqual((f["R1"]["non_english"], f["R1"]["translation_attached"]), (True, False))
        self.assertIn("1.98(a)(3)(i)", f["R1"]["relevance_statement"])
        self.assertEqual((f["R2"]["non_english"], f["R2"]["translation_attached"]), (True, True))
        self.assertEqual(f["R2"]["relevance_statement"], "Shows a frame with stop members (claim 1).")
        self.assertEqual((f["R3"]["non_english"], f["R3"]["translation_attached"]), (False, False))
        self.assertNotIn("relevance_statement", f["R3"])
        self.assertNotIn("translation", f["R1"])
        warns = [x for x in res["findings"] if x["code"] == "relevance_statement_needed"]
        self.assertEqual([x["where"] for x in warns], ["R1"])
        import csv as _csv
        with open(os.path.join(self.d, "draft", "out", "ids.csv"), encoding="utf-8") as fh:
            rows = list(_csv.DictReader(fh))
        by = {r["ref"]: r for r in rows}
        self.assertEqual((by["R1"]["non_english"], by["R1"]["translation_attached"]), ("Y", "N"))
        self.assertEqual(by["R2"]["translation_attached"], "Y")

    def test_ids_tier(self):
        self.assertEqual(ids.tier_for(50), 0)
        self.assertEqual(ids.tier_for(51), 50)
        self.assertEqual(ids.tier_for(150), 100)
        self.assertEqual(ids.tier_for(201), 200)



class TestSearchLogPlan(Base):
    """F16: plan a query before running it; F07: record rewrites and the untrusted-summary note."""

    def setUp(self):
        self.d = make_matter([], elements=[{"id": "E1", "text": "shell", "essential": True},
                                           {"id": "E2", "text": "light", "essential": True}])
        self.base = {"dir": self.d, "no_audit": True}

    def test_plan_then_complete(self):
        r = search_log.run(dict(self.base, command="plan", source="google_patents_web", query="helmet light",
                                elements="E1,E2", date="2026-11-01"))
        self.assertEqual(r["query"]["status"], "planned")
        self.assertNotIn("hits", r["query"])
        search_log.run(dict(self.base, command="plan", source="websearch", query="helmet radio", elements="E2"))
        cov = search_log.run(dict(self.base, command="coverage"))
        self.assertEqual(cov["coverage"]["never_searched"], ["E1", "E2"])  # planned queries do not count
        self.assertEqual(cov["coverage"]["planned_not_run"], ["Q1", "Q2"])
        self.assertEqual(cov["summary"]["planned"], 2)
        self.assertIn("planned, not run: Q1", [f for f in cov["findings"] if f["where"] == "E1"][0]["message"])
        r = search_log.run(dict(self.base, command="add", id="Q1", hits=14, screened=10,
                                results="US9457709B2", date="2026-11-02"))
        q = r["query"]
        self.assertEqual((q["id"], q["status"], q["hits"], q["date"], q["elements"]),
                         ("Q1", "run", 14, "2026-11-02", ["E1", "E2"]))
        self.assertTrue(q["summary_untrusted"])
        cov = search_log.run(dict(self.base, command="coverage"))
        self.assertEqual(cov["coverage"]["never_searched"], [])
        self.assertEqual(cov["coverage"]["planned_not_run"], ["Q2"])
        lst = search_log.run(dict(self.base, command="list"))
        self.assertEqual((lst["summary"]["run"], lst["summary"]["planned"]), (1, 1))
        self.assertTrue(any("PLANNED" in t for t in lst["text"]))
        # a planned query is not a re-run candidate, and completing twice is refused
        plan = search_log.run(dict(self.base, command="rerun-plan", since="2026-11-10"))
        self.assertEqual([p["rerun_of"] for p in plan["plan"]], ["Q1"])
        self.assertIn("planned_not_run", codes(plan, "INFO"))
        with self.assertRaises(search_log.UsageError):
            search_log.run(dict(self.base, command="add", id="Q1", hits=3))
        with self.assertRaises(search_log.UsageError):
            search_log.run(dict(self.base, command="add", id="Q9", hits=3))
        with self.assertRaises(search_log.UsageError):  # different text: use --ran-as
            search_log.run(dict(self.base, command="add", id="Q2", hits=3, query="helmet radio bluetooth"))

    def test_ran_as_and_tool_rewrote(self):
        search_log.run(dict(self.base, command="plan", source="websearch",
                            query='site:patents.google.com helmet "turn signal" Bluetooth', elements="E2"))
        r = search_log.run(dict(self.base, command="add", id="Q1", hits=9, tool_rewrote=True,
                                ran_as='helmet "turn signal"'))
        q = r["query"]
        self.assertEqual(q["query"], 'site:patents.google.com helmet "turn signal" Bluetooth')  # plan kept
        self.assertEqual(q["ran_as"], 'helmet "turn signal"')
        self.assertTrue(q["tool_rewrote"])
        self.assertTrue(any("ran as" in t for t in r["text"]))
        cov = search_log.run(dict(self.base, command="coverage"))
        self.assertIn("rewritten", codes(cov, "INFO"))
        r = search_log.run(dict(self.base, command="add", source="websearch", query="helmet light", hits=2,
                                tool_rewrote=True, summary_untrusted=False))
        self.assertIn("rewrite_unrecorded", codes(r, "WARN"))
        self.assertFalse(r["query"]["summary_untrusted"])
        pa = read_json(os.path.join(self.d, "prior-art.json"))
        self.assertEqual([q.get("status") for q in pa["queries"]], ["run", "run"])

    def test_cli_plan_and_complete(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc1 = search_log.main(["plan", "--dir", self.d, "--no-audit", "--source", "lens", "--query", "x y",
                                   "--elements", "E1"])
            rc2 = search_log.main(["add", "--dir", self.d, "--no-audit", "--id", "Q1", "--hits", "4",
                                   "--no-summary-untrusted"])
        self.assertEqual((rc1, rc2), (0, 0))
        q = read_json(os.path.join(self.d, "prior-art.json"))["queries"][0]
        self.assertEqual((q["status"], q["hits"], q["summary_untrusted"]), ("run", 4, False))



try:
    import fitz  # noqa: F401
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False

COLLINE_PDF = os.path.join(HERE, "fixtures", "colline", "US9457709B2.pdf")
Q_GRANT = "methodology for activating turn signals in a head protection"


class TestQuoteCheckColline(Base):
    """F08: quote_check fills pinpoint_colline from a cached grant PDF (offline); F23: machine
    translations are reported once per reference."""

    def build(self, with_pdf=True):
        refs = [{"id": "R1", "type": "patent", "number": "US9457709B2", "element_map": {
            "E1": {"state": "explicit", "pinpoint": None, "quote": Q_GRANT}}}]
        self.d = make_matter(refs)
        if with_pdf:
            os.makedirs(os.path.join(self.d, "cache", "pdf"))
            shutil.copyfile(COLLINE_PDF, os.path.join(self.d, "cache", "pdf", "US9457709B2.pdf"))

    def entry(self):
        return read_json(os.path.join(self.d, "prior-art.json"))["references"][0]["element_map"]["E1"]

    @unittest.skipUnless(HAVE_FITZ, "PyMuPDF not installed")
    def test_high_confidence_written(self):
        self.build()
        res = quote_check.run({"dir": self.d, "no_audit": True})
        self.assertEqual(res["exit_code"], 0, res["findings"])
        e = self.entry()
        self.assertRegex(e["pinpoint"], r"^p\d+$")       # Google-text pinpoint kept
        self.assertEqual(e["pinpoint_colline"], "col. 2, l. 20")
        self.assertIn("colline pinpoints (US grants)", res["checks_run"])
        self.assertEqual(res["summary"]["colline_filled"], 1)

    def test_no_pdf_is_info_and_skipped(self):
        self.build(with_pdf=False)
        res = quote_check.run({"dir": self.d, "no_audit": True})
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("grant_pdf_not_cached", codes(res, "INFO"))
        self.assertIn("colline pinpoints (US grants)", [s["check"] for s in res["checks_skipped"]])
        self.assertNotIn("pinpoint_colline", self.entry())

    def test_pymupdf_missing_is_skipped_not_fatal(self):
        import colline
        self.build()
        orig = colline.locate_in_cache

        def boom(*a, **k):
            raise quote_check.UsageError("PyMuPDF is required for colline.py: pip3 install pymupdf")
        colline.locate_in_cache = boom
        try:
            res = quote_check.run({"dir": self.d, "no_audit": True})
        finally:
            colline.locate_in_cache = orig
        self.assertEqual(res["exit_code"], 0)
        skipped = {s["check"]: s["reason"] for s in res["checks_skipped"]}
        self.assertTrue(skipped["colline pinpoints (US grants)"].startswith("PyMuPDF missing"))

    def test_not_us_grant_never_calls_colline(self):
        refs = [{"id": "R1", "type": "application", "number": "US20160144773A1", "element_map": {
            "E1": {"state": "explicit", "pinpoint": None,
                   "quote": "The turn signals are included in the adaptive light notification system"}}}]
        self.d = make_matter(refs)
        res = quote_check.run({"dir": self.d, "no_audit": True})
        self.assertEqual({s["check"]: s["reason"] for s in res["checks_skipped"]}["colline pinpoints (US grants)"],
                         "no found US-grant quote with a synthetic pN pinpoint")

    def test_machine_translation_info_once_per_ref(self):
        self.build(with_pdf=False)
        p = os.path.join(self.d, "cache", "US9457709B2.json")
        rec = read_json(p)
        rec["notes"].append("Text is Google machine translation from German; quote it as machine-translated.")
        write_json(p, rec)
        pa = read_json(os.path.join(self.d, "prior-art.json"))
        pa["references"][0]["element_map"]["E2"] = {"state": "partial", "pinpoint": None, "quote": Q_GRANT}
        write_json(os.path.join(self.d, "prior-art.json"), pa)
        res = quote_check.run({"dir": self.d, "no_audit": True})
        mt = [f for f in res["findings"] if f["code"] == "machine_translation"]
        self.assertEqual(len(mt), 1)
        self.assertEqual((mt[0]["level"], mt[0]["where"]), ("INFO", "US9457709B2"))


if __name__ == "__main__":
    unittest.main()
