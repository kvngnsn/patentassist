"""Offline tests for evals/score.py (hard metrics and recall)."""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "evals"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import score  # noqa: E402

class ScoreUnitTest(unittest.TestCase):
    def test_cutoff_violations(self):
        pa = {"references": [
            {"id": "R1", "number": "US9000000B2", "pub_date": "2017-01-01", "prior_art_basis": "102(a)(1)"},
            {"id": "R2", "number": "US20190000001A1", "pub_date": "2019-06-01", "prior_art_basis": "102(a)(1)"},
            {"id": "R3", "number": "US20190000002A1", "pub_date": "2019-06-01", "prior_art_basis": "102(a)(2)",
             "filing_date": "2017-05-01"},
            {"id": "R4", "number": "US20190000003A1", "pub_date": "2019-06-01", "prior_art_basis": "102(a)(2)",
             "filing_date": "2018-05-01"},
            {"id": "R5", "number": "US1"}]}
        r = score.cutoff_violations(pa, "2018-03-01")
        self.assertEqual([v["ref"] for v in r["violations"]], ["R2", "R4"])
        self.assertEqual(r["unchecked"], 1)
        self.assertIsNone(score.cutoff_violations(pa, None)["value"])

    def test_recall_kindless(self):
        tmp = tempfile.mkdtemp()
        try:
            ranked = ["US9000000B1", "EP1000000A1", "US8000000B2"]
            r = score.recall_at(ranked, ["US9000000B2", "US7000000B2"], (1, 3), tmp, False)
            self.assertEqual(r["recall@1"], 0.5)
            self.assertEqual(r["recall@3"], 0.5)
            os.makedirs(os.path.join(tmp, "cache"))
            with open(os.path.join(tmp, "cache", "EP1000000A1.json"), "w") as fh:
                json.dump({"schema": "patentassist/patent@1", "family": ["US7000000B2"]}, fh)
            r = score.recall_at(ranked, ["US9000000B2", "US7000000B2"], (3,), tmp, True)
            self.assertEqual(r["recall@3"], 1.0)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
