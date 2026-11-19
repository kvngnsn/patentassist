"""Offline tests for scripts/oa_parse.py on a synthetic (fictional) non-final office action."""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(HERE, "fixtures", "prosecution")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import oa_parse  # noqa: E402
from state import UsageError  # noqa: E402


def load(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


class TestNonFinal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inv = oa_parse.parse(load("oa_nonfinal.txt"))
        cls.rej = {r["id"]: r for r in cls.inv["rejections"]}

    def test_header(self):
        inv = self.inv
        self.assertEqual(inv["schema"], "patentassist/oa-inventory@1")
        self.assertEqual(inv["app_no"], "18/555,123")
        self.assertEqual(inv["app_no_confidence"], "high")
        self.assertEqual(inv["mailed"], "2026-05-06")
        self.assertEqual(inv["mailed_confidence"], "high")
        self.assertEqual(inv["type"], "nonfinal")
        self.assertEqual(inv["type_confidence"], "high")
        self.assertEqual(inv["art_unit"], "3621")
        self.assertEqual(inv["examiner"], "LEE, MORGAN T")
        self.assertEqual(inv["responsive_to"], "2026-01-10")
        self.assertEqual(inv["ssp_months"], 3)

    def test_summary_dispositions(self):
        c = self.inv["claims"]
        self.assertEqual(c["pending"], list(range(1, 21)))
        self.assertEqual(c["withdrawn"], [16, 17, 18])
        self.assertEqual(c["rejected"], list(range(1, 13)) + [19, 20])
        self.assertEqual(c["objected"], [7, 13, 14, 15])
        self.assertEqual(c["allowed"], [])
        self.assertEqual(c["confidence"], "high")

    def test_rejections(self):
        rs = self.inv["rejections"]
        self.assertEqual([r["basis"] for r in rs], ["ODP", "112(b)", "102", "103", "103"])
        self.assertTrue(all(r["decision"] is None for r in rs))
        odp, r112, r102, r103, r103b = rs
        self.assertEqual(odp["claims"], [1, 10])
        self.assertEqual(odp["double_patenting"], "nonstatutory")
        self.assertEqual(odp["refs"][0]["canonical"], "US11234567")
        self.assertEqual(r112["claims"], [4, 5])
        self.assertEqual(r112["statute"], "35 U.S.C. 112(b)")
        self.assertEqual(r112["refs"], [])
        self.assertEqual(r102["claims"], [1, 2, 3, 6, 10])
        self.assertEqual(r102["statute"], "35 U.S.C. 102(a)(1)")
        self.assertEqual([x["canonical"] for x in r102["refs"]], ["US9123456B2"])
        self.assertEqual(r103["claims"], [4, 5, 7, 8, 9, 11, 12, 19, 20])
        self.assertEqual([(x["name"], x["canonical"], x["role"]) for x in r103["refs"]],
                         [("Smith", "US9123456B2", "primary"), ("Jones", "US20190123456A1", "secondary")])
        # third rejection names Smith and Jones without numbers: resolved from earlier citations
        self.assertEqual(r103b["claims"], [11])
        self.assertEqual([x["canonical"] for x in r103b["refs"]], ["US9123456B2", "US20190123456A1", "KR1020150012345A"])
        self.assertTrue(all(r["confidence"] == "high" for r in rs))

    def test_element_mapping(self):
        m = self.inv["rejections"][2]["mapping"]
        self.assertEqual(len(m), 7)
        first = m[0]
        self.assertEqual((first["claim"], first["element_text"], first["ref"], first["pinpoint"]),
                         (1, "a wearable signaling device", "Smith", "col. 3, ll. 5-10; FIG. 2"))
        texts = [x["element_text"] for x in m if x["claim"] == 1]
        self.assertIn("a flexible band", texts)
        self.assertIn("a controller that activates the light emitter in response to the hand gesture", texts)
        self.assertEqual(m[5]["claim"], 2)
        self.assertEqual(m[5]["element_text"], "the light emitter is an LED array")
        m103 = self.inv["rejections"][3]["mapping"]
        self.assertEqual((m103[0]["claim"], m103[0]["ref"], m103[0]["element_text"], m103[0]["pinpoint"]),
                         (4, "Jones", "a sealed housing enclosing a microcontroller", "para. [0045]; FIG. 3"))
        self.assertEqual(m103[1]["pinpoint"], "para. [0052]-[0055]")
        self.assertEqual(self.inv["rejections"][4]["mapping"][0]["ref"], "Park")
        # nothing is mapped from the Response to Arguments section
        self.assertFalse(any("accelerometer" in x["element_text"] for r in self.inv["rejections"] for x in r["mapping"]))

    def test_objections_and_notes(self):
        ob = self.inv["objections"]
        self.assertEqual([(o["type"], o["subtype"], o["claims"]) for o in ob],
                         [("drawings", None, []), ("claims", "informalities", [7]),
                          ("claims", "allowable_if_rewritten", [13, 14, 15])])
        self.assertEqual(ob[0]["rule"], "37 CFR 1.83(a)")
        self.assertEqual([o["id"] for o in ob], ["O1", "O2", "O3"])
        types = [n["type"] for n in self.inv["notes"]]
        for t in ("112f_interpretation", "withdrawn_rejection", "response_to_arguments", "allowable_subject_matter",
                  "aia_status", "art_of_record_not_relied_upon"):
            self.assertIn(t, types)
        f = next(n for n in self.inv["notes"] if n["type"] == "112f_interpretation")
        self.assertEqual(f["limitations"], [{"text": "signal processing module configured to classify the motion",
                                             "claims": [9]}])
        w = next(n for n in self.inv["notes"] if n["type"] == "withdrawn_rejection")
        self.assertEqual(w["claims"], [6])
        ra = next(n for n in self.inv["notes"] if n["type"] == "response_to_arguments")
        self.assertIn("not persuasive", ra["text"])
        self.assertIsNone(self.inv["restriction"])

    def test_run_writes_inventory(self):
        d = tempfile.mkdtemp()
        try:
            out = os.path.join(d, "patent", "prosecution", "oa-2026-05-06", "inventory.json")
            os.makedirs(os.path.join(d, "patent"))
            res = oa_parse.run({"input": os.path.join(FIX, "oa_nonfinal.txt"), "out": out,
                                "dir": os.path.join(d, "patent")})
            self.assertEqual(res["exit_code"], 0)
            with open(out) as fh:
                inv = json.load(fh)
            self.assertEqual(len(inv["rejections"]), 5)
            with open(os.path.join(d, "patent", "audit.jsonl")) as fh:
                rec = json.loads(fh.readline())
            self.assertEqual(rec["kind"], "export")
            self.assertTrue(any("deadlines.py oa --mailed 2026-05-06 --type nonfinal" in t for t in res["text"]))
        finally:
            shutil.rmtree(d)


class TestVariants(unittest.TestCase):
    def test_final_and_checkbox(self):
        t = load("oa_nonfinal.txt").replace("2a)☐ This action is FINAL.                2b)☒ This action is non-final.",
                                            "2a)☒ This action is FINAL.                2b)☐ This action is non-final.")
        t = t.replace("Conclusion\n", "Conclusion\n\nApplicant's amendment necessitated the new ground(s) of rejection. "
                                      "Accordingly, THIS ACTION IS MADE FINAL. See MPEP § 706.07(a).\n", 1)
        inv = oa_parse.parse(t)
        self.assertEqual((inv["type"], inv["type_confidence"]), ("final", "high"))

    def test_restriction(self):
        t = ("Application/Control Number: 18/000,777\nOffice Action Summary\nDETAILED ACTION\n\nElection/Restrictions\n\n"
             "1.  Restriction to one of the following inventions is required under 35 U.S.C. 121:\n"
             "    I. Claims 1-8, drawn to a wearable band, classified in CPC G08G 1/005.\n"
             "    II. Claims 9-12, drawn to a charging dock, classified in CPC H02J 7/00.\n\n"
             "2.  The inventions are independent or distinct, each from the other.\n")
        inv = oa_parse.parse(t)
        self.assertEqual(inv["type"], "restriction")
        self.assertEqual([(g["group"], g["claims"]) for g in inv["restriction"]["groups"]],
                         [("I", list(range(1, 9))), ("II", [9, 10, 11, 12])])
        self.assertEqual(inv["app_no"], "18/000,777")
        self.assertEqual(inv["claims"]["confidence"], "low")

    def test_low_confidence_flags(self):
        t = ("DETAILED ACTION\n\nClaim Rejections - 35 USC § 103\n\n1.  Claims 1-3 are rejected under 35 U.S.C. 103 as "
             "being unpatentable over Doe in view of Roe.\n")
        inv = oa_parse.parse(t)
        r = inv["rejections"][0]
        self.assertEqual(r["confidence"], "low")
        self.assertEqual([x["name"] for x in r["refs"]], ["Doe", "Roe"])
        self.assertIsNone(inv["mailed"])
        self.assertTrue(any(w["where"] == "mailed" for w in inv["parse_warnings"]))

    def test_expand_claims(self):
        self.assertEqual(oa_parse.expand_claims("1-12,19 and 20"), list(range(1, 13)) + [19, 20])
        self.assertEqual(oa_parse.expand_claims("1 through 3, 5"), [1, 2, 3, 5])
        self.assertEqual(oa_parse.expand_claims("____"), [])

    def test_not_an_oa(self):
        with self.assertRaises(UsageError):
            oa_parse.run({"text": "Grocery list: eggs, milk."})


if __name__ == "__main__":
    unittest.main()
