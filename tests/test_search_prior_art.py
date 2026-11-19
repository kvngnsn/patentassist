"""Offline tests for scripts/prior_art.py (F12 element/cutoff/ref/cell/combo editing, F19 vocabulary,
F06 purpose-free element tests) and its hand-off to verify_refs.py."""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import prior_art  # noqa: E402
import verify_refs  # noqa: E402
from patent_fetch import parse_google_html  # noqa: E402
from state import UsageError, empty_prior_art, read_json, write_json  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "search")


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.d, "cache"))
        write_json(os.path.join(self.d, "prior-art.json"), empty_prior_art())

    def tearDown(self):
        shutil.rmtree(self.d)

    def pa(self, **kw):
        args = {"dir": self.d, "no_audit": True}
        args.update(kw)
        return prior_art.run(args)

    def doc(self):
        return read_json(os.path.join(self.d, "prior-art.json"))

    def codes(self, res, level=None):
        return [f["code"] for f in res["findings"] if level is None or f["level"] == level]


class TestElements(Base):
    def test_add_set_list_and_test_field(self):
        r = self.pa(command="elements", action="add", text="a helmet shell")
        self.assertEqual(r["element"], {"id": "E1", "text": "a helmet shell", "essential": True})
        self.pa(command="elements", action="add", text="a pre-boil-over signature", essential="false",
                test="dominant band shifts and total level rises above a limit, held for N intervals")
        r = self.pa(command="elements", action="set", id="E1", test="a rigid shell worn on the head")
        self.assertEqual(r["element"]["test"], "a rigid shell worn on the head")
        els = self.doc()["elements"]
        self.assertEqual([e["id"] for e in els], ["E1", "E2"])
        self.assertFalse(els[1]["essential"])
        r = self.pa(command="elements", action="set", id="E2", test="detects it so that boil-over is prevented")
        self.assertIn("purpose_words", self.codes(r, "WARN"))
        self.pa(command="elements", action="set", id="E2", test="")
        self.assertNotIn("test", self.doc()["elements"][1])
        r = self.pa(command="elements", action="list")
        self.assertIn("no_test", self.codes(r, "INFO"))
        self.assertEqual(r["summary"]["with_test"], 1)
        with self.assertRaises(UsageError):
            self.pa(command="elements", action="add", text="dup", id="E1")
        with self.assertRaises(UsageError):
            self.pa(command="elements", action="set", id="E7", text="x")
        with self.assertRaises(UsageError):
            self.pa(command="elements", action="set", id="E1", essential="maybe")


class TestCutoffVocabulary(Base):
    def test_cutoff(self):
        r = self.pa(command="cutoff", date="2026-11-18", basis="no disclosure; today's date")
        self.assertEqual(r["cutoff"]["cutoff_date"], "2026-11-18")
        self.assertEqual(self.doc()["cutoff_basis"], "no disclosure; today's date")
        for bad in ({"date": "11/18/2026", "basis": "x"}, {"date": "2026-11-18", "basis": " "}):
            with self.assertRaises(UsageError):
                self.pa(command="cutoff", **bad)

    def test_vocabulary_confirmation(self):
        with self.assertRaises(UsageError):  # no elements yet
            self.pa(command="vocabulary", action="set", id="E1", terms="a|b")
        self.pa(command="elements", action="add", text="vibration sensor")
        r = self.pa(command="vocabulary", action="set", id="E1", terms="vibration | acoustic|Vibration|piezo")
        self.assertEqual(r["vocabulary"]["E1"], {"terms": ["vibration", "acoustic", "piezo"],
                                                 "confirmed_by_user": False})
        self.pa(command="vocabulary", action="set", id="E1", terms="vibration|acoustic|piezo", confirmed=True)
        # same terms again without --confirmed keeps the confirmation; new terms reset it
        self.pa(command="vocabulary", action="set", id="E1", terms="vibration|acoustic|piezo")
        self.assertTrue(self.doc()["vocabulary"]["E1"]["confirmed_by_user"])
        self.pa(command="vocabulary", action="set", id="E1", terms="vibration|accelerometer")
        self.assertFalse(self.doc()["vocabulary"]["E1"]["confirmed_by_user"])
        with self.assertRaises(UsageError):
            self.pa(command="vocabulary", action="set", id="E9", terms="x")


class TestRefsCellsCombos(Base):
    def setUp(self):
        Base.setUp(self)
        for t in ("helmet shell", "rear lights", "wireless switch"):
            self.pa(command="elements", action="add", text=t)

    def test_ref_add_infers_type_and_rejects_duplicates(self):
        r = self.pa(command="ref", action="add", number="US 2016/0144773 A1", category="y")
        self.assertEqual(r["reference"], {"id": "R1", "type": "application", "number": "US20160144773A1",
                                          "category": "Y", "verified": False, "element_map": {}})
        self.assertEqual(self.pa(command="ref", action="add", number="9457709")["reference"]["type"], "patent")
        r = self.pa(command="ref", action="add", number="https://doi.org/10.1121/1.1566333")
        self.assertEqual((r["reference"]["type"], r["reference"]["doi"]), ("npl", "10.1121/1.1566333"))
        r = self.pa(command="ref", action="add", number="https://example.com/helmet", type="product")
        self.assertEqual((r["reference"]["type"], r["reference"]["url"]), ("product", "https://example.com/helmet"))
        with self.assertRaises(UsageError):  # same document, different kind
            self.pa(command="ref", action="add", number="US20160144773")
        with self.assertRaises(UsageError):
            self.pa(command="ref", action="add", number="10.1121/1.1566333")
        with self.assertRaises(UsageError):
            self.pa(command="ref", action="add", number="EP1000000B1", category="Z")
        with self.assertRaises(UsageError):
            self.pa(command="ref", action="add", number="not a number")
        with self.assertRaises(UsageError):  # application numbers are not citable
            self.pa(command="ref", action="add", number="14/552,936")

    def test_ref_add_moves_out_of_read_not_cited(self):
        self.pa(command="read-not-cited", action="add", number="US8803674B2", why="bicycle lights")
        r = self.pa(command="ref", action="add", number="US8803674B2")
        self.assertIn("moved_from_read_not_cited", self.codes(r, "INFO"))
        self.assertEqual(self.doc()["read_not_cited"], [])
        with self.assertRaises(UsageError):
            self.pa(command="read-not-cited", action="add", number="US8803674", why="x")

    def test_cell_set_validates_and_keeps_derived_fields(self):
        self.pa(command="ref", action="add", number="US9457709B2", category="X")
        r = self.pa(command="cell", action="set", ref="R1", element="E2", state="partial", pinpoint="p17",
                    quote="turn signals", note="not LEDs", construction_dependent=True)
        self.assertEqual(r["cell"]["entry"], {"state": "partial", "pinpoint": "p17", "quote": "turn signals",
                                              "note": "not LEDs", "construction_dependent": True})
        doc = self.doc()
        doc["references"][0]["element_map"]["E2"]["pinpoint_colline"] = "col. 2, l. 20"
        write_json(os.path.join(self.d, "prior-art.json"), doc)
        self.pa(command="cell", action="set", ref="R1", element="E2", state="explicit", pinpoint="p17",
                quote="turn signals")
        self.assertEqual(self.doc()["references"][0]["element_map"]["E2"]["pinpoint_colline"], "col. 2, l. 20")
        self.pa(command="cell", action="set", ref="R1", element="E2", state="explicit", quote="other words")
        self.assertNotIn("pinpoint_colline", self.doc()["references"][0]["element_map"]["E2"])
        r = self.pa(command="cell", action="set", ref="R1", element="E3", state="explicit", pinpoint="line 4")
        self.assertIn("quote_missing", self.codes(r, "WARN"))
        self.assertIn("pinpoint_format", self.codes(r, "WARN"))
        r = self.pa(command="cell", action="set", ref="R1", element="E1", state="unknown")
        self.assertEqual(r["cell"]["entry"], {"state": "unknown", "pinpoint": None, "quote": None})
        for bad in ({"ref": "R1", "element": "E1", "state": "maybe"}, {"ref": "R9", "element": "E1", "state": "absent"},
                    {"ref": "R1", "element": "E9", "state": "absent"}):
            with self.assertRaises(UsageError):
                self.pa(command="cell", action="set", **bad)

    def test_combo_lists_and_audit(self):
        self.pa(command="ref", action="add", number="US9457709B2")
        self.pa(command="ref", action="add", number="EP1000000B1")
        r = prior_art.run({"dir": self.d, "command": "combo", "action": "add", "refs": "R1,R2", "covers": "E1,E2",
                           "rationale": "KSR (G)", "strength": "strong"})
        self.assertIn("elements_not_covered", self.codes(r, "INFO"))
        self.assertEqual(self.doc()["combinations"], [{"refs": ["R1", "R2"], "covers": ["E1", "E2"],
                                                       "rationale": "KSR (G)", "strength": "strong"}])
        with open(os.path.join(self.d, "audit.jsonl"), encoding="utf-8") as fh:
            last = json.loads(fh.read().strip().splitlines()[-1])
        self.assertEqual((last["kind"], last["action"]), ("note", "prior_art.combo.add"))
        for bad in ({"refs": "R1", "covers": "E1", "rationale": "x", "strength": "strong"},
                    {"refs": "R1,R2", "covers": "E1", "rationale": "x", "strength": "certain"},
                    {"refs": "R1,R2", "covers": "E1", "rationale": " ", "strength": "weak"}):
            with self.assertRaises(UsageError):
                self.pa(command="combo", action="add", **bad)
        self.pa(command="not-searched", action="add", text="paid databases")
        self.pa(command="not-searched", action="add", text="Paid databases")
        self.assertEqual(self.doc()["not_searched"], ["paid databases"])

    def test_cli_needs_action(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(prior_art.main(["--dir", self.d, "elements"]), 2)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(prior_art.main(["cell", "set", "R1", "E1", "--state", "absent", "--dir", self.d]), 2)


class TestStubThenVerify(Base):
    """A `ref add` stub is filled in by verify_refs.py from the cache."""

    def test_verify_fills_stub(self):
        with open(os.path.join(FIX, "US9457709B2.html"), encoding="utf-8") as fh:
            write_json(os.path.join(self.d, "cache", "US9457709B2.json"),
                       parse_google_html(fh.read(), requested="US9457709B2"))
        self.pa(command="cutoff", date="2017-01-01", basis="test")
        self.pa(command="ref", action="add", number="US9457709B2", category="X")
        res = verify_refs.run({"dir": self.d, "offline": True, "no_audit": True, "today": "2026-11-18"})
        self.assertEqual(res["exit_code"], 0, res["findings"])
        r = self.doc()["references"][0]
        self.assertTrue(r["verified"])
        self.assertTrue(r["title"].startswith("Bicycle helmet"))
        self.assertEqual(r["prior_art_basis"], "102(a)(1)")
        self.assertEqual(r["category"], "X")


if __name__ == "__main__":
    unittest.main()
