"""Offline tests for scripts/oa_check.py: completeness against the inventory, 37 CFR 1.121(c) markup,
new-matter word check, and clean claims."""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures", "prosecution")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import oa_check  # noqa: E402
import oa_parse  # noqa: E402
from state import write_json  # noqa: E402


def fx(name):
    return os.path.join(FIX, name)


def codes(res, level=None):
    return [f["code"] for f in res["findings"] if level is None or f["level"] == level]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        with open(fx("oa_nonfinal.txt"), encoding="utf-8") as fh:
            cls.inv_obj = oa_parse.parse(fh.read())
        cls.inv = os.path.join(cls.tmp, "inventory.json")
        write_json(cls.inv, cls.inv_obj)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def run_cmd(self, **kw):
        kw.setdefault("no_audit", True)
        return oa_check.run(kw)


class TestGoodResponse(Base):
    def test_all_passes(self):
        res = self.run_cmd(command="all", inventory=self.inv, response=fx("response_good.md"), spec=fx("spec.md"),
                           previous_claims=fx("claims_previous.md"))
        self.assertEqual(codes(res, "BLOCK"), [])
        self.assertEqual(codes(res, "WARN"), [])
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("markup:new_numbering_full", res["checks_run"])
        self.assertIn("NOTE_112F", codes(res, "INFO"))

    def test_markup_without_previous_warns(self):
        res = self.run_cmd(command="markup", response=fx("response_good.md"))
        self.assertEqual(codes(res, "BLOCK"), [])
        self.assertIn("NEW_NUMBERING_UNVERIFIED", codes(res, "WARN"))
        self.assertTrue(any(s["check"] == "markup:new_numbering_full" for s in res["checks_skipped"]))
        self.assertIn("not a clean bill", "\n".join(res["text"]))

    def test_clean(self):
        out = os.path.join(self.tmp, "clean_claims.md")
        res = self.run_cmd(command="clean", response=fx("response_good.md"), out=out)
        with open(out) as fh:
            text = fh.read()
        self.assertIn("1. A wearable signaling device comprising:", text)
        self.assertIn("in response to the hand gesture, wherein the controller selects a blink pattern based on a "
                      "direction of the hand gesture.", text)
        self.assertIn("4. The wearable signaling device of claim 1, wherein a housing encloses the controller.", text)
        self.assertIn("5. The wearable signaling device of claim 4, wherein the housing is rigid.", text)
        self.assertIn("reads the sensor at", text)
        self.assertIn("6. (Canceled)", text)
        self.assertIn("16. (Withdrawn) A charging dock", text)
        self.assertNotIn("<u>", text)
        self.assertNotIn("~~", text)
        self.assertNotIn("[[", text)
        self.assertEqual(res["kept"], [1, 2, 3, 4, 5] + list(range(7, 22)))


class TestBadResponse(Base):
    def test_inventory_completeness(self):
        res = self.run_cmd(command="inventory", inventory=self.inv, response=fx("response_bad.md"))
        blocks = [(f["code"], f["where"].split()[0]) for f in res["findings"] if f["level"] == "BLOCK"]
        self.assertIn(("REJECTION_UNANSWERED", "R1"), blocks)   # double patenting not answered
        self.assertIn(("REJECTION_UNANSWERED", "R2"), blocks)   # 112(b) not answered
        self.assertNotIn(("REJECTION_UNANSWERED", "R3"), blocks)
        self.assertIn(("OBJECTION_UNANSWERED", "O1"), blocks)   # drawings
        self.assertIn(("OBJECTION_UNANSWERED", "O2"), blocks)   # claim 7 informality not fixed
        self.assertIn(("CLAIM_UNANSWERED", "claim"), blocks)
        self.assertIn(("LISTING_INCOMPLETE", "listing"), blocks)  # claim 9 dropped
        self.assertEqual(res["exit_code"], 1)

    def test_inventory_decisions_count(self):
        import json
        inv = json.loads(json.dumps(self.inv_obj))
        for r in inv["rejections"]:
            if r["id"] in ("R1", "R2"):
                r["decision"] = "interview first"
        p = os.path.join(self.tmp, "inv_decided.json")
        write_json(p, inv)
        res = self.run_cmd(command="inventory", inventory=p, response=fx("response_bad.md"))
        self.assertNotIn("REJECTION_UNANSWERED", codes(res, "BLOCK"))
        self.assertIn("DECISION", codes(res, "INFO"))

    def test_markup_rules(self):
        res = self.run_cmd(command="markup", response=fx("response_bad.md"), previous_claims=fx("claims_previous.md"))
        by = {}
        for f in res["findings"]:
            by.setdefault(f["code"], []).append(f["where"])
        self.assertEqual(by["MARKUP_NOT_ALLOWED"], ["claim 2"])        # markup in an (Original) claim
        self.assertEqual(by["DOUBLE_BRACKET_LONG"], ["claim 5"])       # [[substantially]] > 5 characters
        self.assertEqual(by["CANCELED_TEXT"], ["claim 6"])
        self.assertEqual(by["STATUS_MULTIPLE"], ["claim 12"])
        self.assertEqual(by["STATUS_UNKNOWN"], ["claim 13"])
        self.assertEqual(by["LISTING_ORDER"], ["claim 11"])
        self.assertEqual(by["LISTING_INCOMPLETE"], ["listing"])
        self.assertEqual(by["NEW_HAS_MARKUP"], ["claim 21"])
        self.assertEqual(by["DEP_CANCELED"], ["claim 20"])
        self.assertIn("claim 20", by["UNCHANGED_DIFFERS"])
        self.assertNotIn("claim 4", sum(by.values(), []))              # [[the]] <u>a</u> is correct
        levels = {f["code"]: f["level"] for f in res["findings"]}
        self.assertEqual(levels["DOUBLE_BRACKET_LONG"], "WARN")
        self.assertEqual(levels["CANCELED_TEXT"], "BLOCK")

    def test_new_claim_numbering_with_previous_listing(self):
        prev = self.write("prev_listing.md", "## AMENDMENTS TO THE CLAIMS\n\n1. (Original) A cup.\n\n"
                                             "2. (Original) The cup of claim 1, wherein it is blue.\n\n3. (Canceled)\n\n"
                                             "4. (Original) The cup of claim 1, wherein it is tall.\n")
        resp = self.write("resp_num.md", "## AMENDMENTS TO THE CLAIMS\n\n1. (Original) A cup.\n\n"
                                         "2. (Original) The cup of claim 1, wherein it is blue.\n\n"
                                         "3. (New) The cup of claim 1, wherein it is red.\n\n"
                                         "4. (Original) The cup of claim 1, wherein it is tall.\n\n"
                                         "6. (New) The cup of claim 1, wherein it is short.\n")
        res = self.run_cmd(command="markup", response=resp, previous_claims=prev)
        c = codes(res, "BLOCK")
        self.assertIn("NEW_REUSES_NUMBER", c)          # claim 3 was canceled; cannot be reused
        self.assertIn("NEW_NUMBERING", c)              # next new number is 5, not 6
        self.assertIn("LISTING_INCOMPLETE", c)         # claim 5 missing
        ok = self.write("resp_num_ok.md", "## AMENDMENTS TO THE CLAIMS\n\n1. (Original) A cup.\n\n"
                                          "2. (Currently Amended) The cup of claim 1, wherein it is ~~blue~~ <u>green</u>."
                                          "\n\nClaims 3-4 (Canceled)\n\n5. (New) The cup of claim 1, wherein it is red.\n")
        res = self.run_cmd(command="markup", response=ok, previous_claims=prev)
        self.assertEqual(codes(res, "BLOCK"), [])
        self.assertEqual(codes(res, "WARN"), [])


class TestNewMatter(Base):
    def test_added_word_absent_from_spec(self):
        res = self.run_cmd(command="newmatter", claims=fx("response_bad.md"), spec=fx("spec.md"))
        words = [f["message"] for f in res["findings"] if f["code"] == "NEWMATTER_WORD"]
        self.assertTrue(any("'titanium'" in m for m in words))
        self.assertTrue(any("'organic'" in m for m in words))
        self.assertFalse(any("'elastic'" in m or "'strap'" in m for m in words))   # claim 21 is supported
        self.assertEqual(res["exit_code"], 1)
        self.assertEqual(res["newmatter"][1]["unsupported_words"], ["titanium"])

    def test_normalization_and_diff(self):
        spec = self.write("spec_small.md", "The light-emitting diodes blink. Batteries power the wrist band.")
        prev = self.write("prev_small.md", "1. A device comprising a light.\n")
        amended = self.write("amended_small.md", "1. A device comprising a light emitting diode, a battery, a "
                                                 "wristband, and a gyroscope.\n")
        res = self.run_cmd(command="newmatter", claims=amended, spec=spec, previous_claims=prev)
        bad = [f["message"] for f in res["findings"] if f["code"] == "NEWMATTER_WORD"]
        self.assertEqual(len(bad), 1)
        self.assertIn("'gyroscope'", bad[0])          # plural, hyphen, and joined forms all pass
        res = self.run_cmd(command="newmatter", claims=amended, spec=spec)
        self.assertTrue(any(s["check"] == "newmatter:added_text" for s in res["checks_skipped"]))

    def test_phrase_warning(self):
        spec = self.write("spec_phrase.md", "The strap is elastic. A blue lens covers the lamp.")
        resp = self.write("resp_phrase.md", "## AMENDMENTS TO THE CLAIMS\n\n1. (Currently Amended) A lamp comprising "
                                            "a lens<u> and an elastic lens strap</u>.\n")
        res = self.run_cmd(command="newmatter", claims=resp, spec=spec)
        self.assertEqual(codes(res, "BLOCK"), [])
        self.assertIn("NEWMATTER_PHRASE", codes(res, "WARN"))


if __name__ == "__main__":
    unittest.main()
