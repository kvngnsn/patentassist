"""Offline tests for scripts/check_package.py (builds a temporary matter folder from the clean fixtures)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FIX = os.path.join(HERE, "fixtures", "draft")
# One fixture defines the patentassist/filing@1 contract (references/state-files.md): build/filing.json.
FILING = os.path.join(HERE, "fixtures", "build", "filing.json")
sys.path.insert(0, SCRIPTS)

import check_package as cp  # noqa: E402
import review


def draft_filing(**over):
    """build/filing.json adapted to the clean draft fixtures: their title, a nonprovisional, one complete
    inventor, small entity. Every field keeps the documented names (given/family, mailing{})."""
    with open(FILING) as fh:
        f = json.load(fh)
    f.update({"filing_type": "nonprovisional", "title": "Helmet Turn Signal System With Handlebar Switches",
              "entity_status": "small", "micro_basis": None, "inventors": f["inventors"][:1]})
    f.update(over)
    return f


def make_matter(tmp, **filing_over):
    d = os.path.join(tmp, "patent")
    os.makedirs(os.path.join(d, "draft"))
    for src, dst in (("clean_claims.md", "claims.md"), ("clean_spec.md", "spec.md"),
                     ("clean_figures.json", "figures.json")):
        shutil.copy(os.path.join(FIX, src), os.path.join(d, "draft", dst))
    with open(os.path.join(d, "draft", "filing.json"), "w") as fh:
        json.dump(draft_filing(**filing_over), fh, indent=2)
    st = os.path.join(SCRIPTS, "state.py")
    subprocess.run([sys.executable, st, "init", "--title", "Helmet", "--mode", "inventor", "--dir", d],
                   check=True, capture_output=True)
    with open(os.path.join(d, "invention-disclosure.md"), "w") as fh:
        fh.write("Synthetic fixture: helmet signal with handlebar controls.\n")
    with open(os.path.join(d, "draft", "support-map.md"), "w") as fh:
        fh.write("Synthetic fixture claims map to the helmet, lights, controller and switch disclosure.\n")
    review.record(d, "draft", {
        "purpose": "patentability", "outcome": "inconclusive", "scope_confirmed": True,
        "scope": "Synthetic helmet fixture claims, current version.",
        "bottom_line": "Patentability unassessed; this fixture tests document mechanics.",
        "examiner_objection": "No search record establishes novelty or nonobviousness.",
        "applicant_response": "No substantive response is asserted in this fixture.",
        "resolution": "No legal conclusion; test only the export mechanics.",
        "next_action": "Complete research before relying on these claims.",
        "uncertainty": "No prior-art search was performed.",
        "inventor_fidelity": "Synthetic source and draft use the same disclosed components.",
        "proceed_basis": "Synthetic test author requests an unsearched draft fixture.",
        "coverage": {"search": "none", "limits": ["Synthetic test, no real patentability assessment."]},
        "grounds": [], "reference_ids": []})
    subprocess.run([sys.executable, st, "hash", "--dir", d], check=True, capture_output=True)
    return d


class TestPackage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.d = make_matter(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_pkg(self):
        return cp.run({"dir": self.d, "no_audit": True})

    def blocks(self, res):
        return {f["code"] for f in res["findings"] if f["level"] == "BLOCK"}

    def test_clean_package_ready(self):
        res = self.run_pkg()
        self.assertEqual(self.blocks(res), set(), res["findings"])
        self.assertTrue(res["summary"]["ready_to_export"], res["summary"]["not_ready_reasons"])
        for c in ("check_claims", "check_spec", "STALE", "MARKERS", "TITLE_MATCH", "INVENTORS", "ENTITY"):
            self.assertIn(c, res["checks_run"])
        self.assertEqual(res["summary"]["counts"]["independent"], 3)

    def test_seeded_package_errors(self):
        out = os.path.join(self.d, "draft", "out")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "spec.md"), "w") as fh:
            fh.write("built copy\n")
        with open(os.path.join(out, "fee-sheet.md"), "w") as fh:
            fh.write("# Fee sheet\n\n3 independent, 18 total for fees\n")
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "state.py"), "hash", "--dir", self.d],
                       check=True, capture_output=True)
        cl = os.path.join(self.d, "draft", "claims.md")
        with open(cl, "a") as fh:
            fh.write("\n19. The system of claim 8, wherein the helmet is a bicycle helmet.\n")
        sp = os.path.join(self.d, "draft", "spec.md")
        with open(sp) as fh:
            s = fh.read()
        s = s.replace("Not applicable.", "Not applicable. TODO add the priority claim [inventor to confirm].")
        s = s.replace("See claims.md.", "1. A helmet comprising a shell.")
        with open(sp, "w") as fh:
            fh.write(s)
        fp = os.path.join(self.d, "draft", "filing.json")
        with open(fp) as fh:
            f = json.load(fh)
        f.update({"title": "Another Title", "inventors": [], "entity_status": None})
        with open(fp, "w") as fh:
            json.dump(f, fh)
        res = self.run_pkg()
        got = self.blocks(res)
        for code in ("STALE", "MARKERS", "CLAIMS_MATCH", "TITLE_MATCH", "INVENTORS", "ENTITY", "FEE_COUNTS"):
            self.assertIn(code, got)
        self.assertFalse(res["summary"]["ready_to_export"])
        self.assertEqual(res["exit_code"], 1)

    def test_missing_script_is_skipped_not_crashed(self):
        res = self.run_pkg()
        names = [s["check"] for s in res["checks_skipped"]]
        self.assertIn("FEE_COUNTS", names)  # no fee sheet built yet: recorded, not fatal

    def test_cli_text(self):
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_package.py"), "--dir", self.d, "--no-audit"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("Ready to export: yes", p.stdout)


if __name__ == "__main__":
    unittest.main()


class TestFilingSchemaNames(unittest.TestCase):
    """Dogfooding: a filing.json written to the documented patentassist/filing@1 schema
    (given / middle / family, mailing {...}) got 'inventor 1 has no legal name' (BLOCK)."""

    def test_given_family_and_mailing_object(self):
        inv = {"given": "Dana", "middle": "R.", "family": "Whitfield",
               "residence": {"city": "Portland", "state": "OR", "country": "US"},
               "mailing": {"address1": "100 Example Avenue", "city": "Portland", "state": "OR",
                           "postcode": "97201", "country": "US"}}
        self.assertEqual(cp._inventor_name(inv), "Dana R. Whitfield")


class TestPackageNoise(unittest.TestCase):
    """Dogfooding (F37, F38): worksheet legends flagged as markers, FEE_COUNTS on a provisional, a wrong
    CLAIMS_MATCH skip reason, and "Ready to export: yes" with claimed features in no figure."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_provisional_worksheet_and_fee_sheet(self):
        d = make_matter(self.tmp, filing_type="provisional")
        out = os.path.join(d, "draft", "out")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "sb16-worksheet.md"), "w") as fh:
            fh.write("# SB/16 worksheet\n\n`[ask user]` means filing.json has no value yet.\n")
        with open(os.path.join(out, "fees.md"), "w") as fh:
            fh.write("# Fee estimate\n\nProvisional filing fee $130\n")
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "state.py"), "hash", "--dir", d],
                       check=True, capture_output=True)
        res = cp.run({"dir": d, "no_audit": True})
        self.assertFalse([f for f in res["findings"] if f["code"] in ("MARKERS", "FEE_COUNTS")], res["findings"])
        reasons = {s["check"]: s["reason"] for s in res["checks_skipped"]}
        self.assertIn("provisional", reasons["FEE_COUNTS"])
        self.assertIn("worksheet", reasons["MARKERS draft/out/sb16-worksheet.md"])
        self.assertIn("points to claims.md", reasons["CLAIMS_MATCH"])

    def test_claimed_feature_not_in_any_figure(self):
        d = make_matter(self.tmp)
        with open(os.path.join(d, "draft", "claims.md"), "a") as fh:
            fh.write("\n19. The system of claim 8, further comprising a solar panel mounted on the shell.\n")
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "state.py"), "hash", "--dir", d],
                       check=True, capture_output=True)
        res = cp.run({"dir": d, "no_audit": True})
        warns = [f for f in res["findings"] if f["code"] == "CLAIMED_NOT_SHOWN"]
        self.assertTrue(any("solar panel" in f["message"] and f["where"].endswith("claim 19") for f in warns), warns)
        self.assertFalse(any('"shell"' in f["message"] for f in warns))   # drawn in FIG. 1
        self.assertIn("CLAIMED_NOT_SHOWN", res["checks_run"])
        if res["summary"]["ready_to_export"]:
            self.assertEqual(res["summary"]["ready_label"], "yes, with warnings")
            self.assertIn("Ready to export: yes, with warnings", cp.render_text(res))
