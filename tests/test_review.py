"""Review invariants: candid outcomes, coverage, provenance, freshness and package enforcement."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import review
from state import UsageError


def assessment(outcome="inconclusive"):
    return {
        "purpose": "patentability", "outcome": outcome, "scope_confirmed": True,
        "scope": "Confirmed sensor, controller and warning-light combination.",
        "bottom_line": "Current combination remains unresolved on this limited record.",
        "examiner_objection": "The recorded source describes the same arrangement.",
        "applicant_response": "No persuasive distinction has been identified.",
        "resolution": "The supplied record determines the stated conditional outcome.",
        "next_action": "Confirm source dates and the user's actual remaining distinctions.",
        "uncertainty": "No foreign or nonpatent search has been completed.",
        "inventor_fidelity": "All features trace to the synthetic disclosure.",
        "proceed_basis": "Test user requested a draft despite stated search limits.",
        "coverage": {"search": "limited", "limits": ["Synthetic fixture, limited sources."]},
        "grounds": [], "reference_ids": [],
    }


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.d.joinpath("invention-disclosure.md").write_text("Synthetic sensor arrangement.")
        self.art = {"schema": "patentassist/prior-art@1", "references": [{
            "id": "R1", "verified": True, "verified_how": "Synthetic test verifier fixture only",
            "verified_on": "2026-11-19"}]}
        self.write_art()

    def write_art(self):
        self.d.joinpath("prior-art.json").write_text(json.dumps(self.art))

    def test_candid_adverse_outcome_is_allowed_with_evidence(self):
        a = assessment("likely_unpatentable")
        a.update(grounds=["102"], reference_ids=["R1"])
        review.record(self.d, "lite", a)
        self.assertEqual(review.check(self.d, "lite")["outcome"], "likely_unpatentable")

    def test_limited_no_hit_cannot_support_favorable_outcome(self):
        a = assessment("likely_patentable")
        for phase in ("lite", "deep", "draft"):
            with self.subTest(phase=phase), self.assertRaises(UsageError):
                review.validate(a, phase, self.d)

    def test_qualified_favorable_allowed_after_substantial_review(self):
        a = assessment("likely_patentable")
        a["coverage"]["search"] = "substantial"
        review.record(self.d, "deep", a)
        self.assertEqual(review.check(self.d, "deep")["outcome"], "likely_patentable")

    def test_favorable_requires_confirmed_scope(self):
        a = assessment("likely_patentable")
        a["coverage"]["search"] = "substantial"
        a["scope_confirmed"] = False
        with self.assertRaises(UsageError):
            review.validate(a, "deep", self.d)

    def test_phase_zero_does_not_claim_novelty_review(self):
        a = assessment("needs_clarification")
        a["coverage"]["search"] = "none"
        review.record(self.d, "clarify", a)
        for change in ({"outcome": "likely_unpatentable"}, {"grounds": ["103"]},
                       {"reference_ids": ["R1"]}, {"coverage": {"search": "limited", "limits": ["test"]}}):
            with self.subTest(change=change), self.assertRaises(UsageError):
                review.validate(dict(a, **change), "clarify", self.d)

    def test_no_search_cannot_be_called_no_blocker_found(self):
        a = assessment("no_blocker_found")
        a["coverage"]["search"] = "none"
        with self.assertRaises(UsageError):
            review.validate(a, "lite", self.d)

    def test_prior_art_requires_verified_source_record(self):
        a = assessment("likely_unpatentable")
        a.update(grounds=["103"], reference_ids=["R1"])
        for field in ("verified", "verified_how", "verified_on"):
            saved = self.art["references"][0].pop(field)
            self.write_art()
            with self.subTest(field=field), self.assertRaises(UsageError):
                review.validate(a, "deep", self.d)
            self.art["references"][0][field] = saved
        self.write_art()
        a["reference_ids"] = ["R99"]
        with self.assertRaises(UsageError):
            review.validate(a, "deep", self.d)

    def test_non_art_adverse_assessment_does_not_require_fake_art(self):
        a = assessment("likely_unpatentable")
        a.update(grounds=["101"], reference_ids=[])
        a["coverage"]["search"] = "none"
        review.record(self.d, "deep", a)
        self.assertEqual(review.check(self.d, "deep")["reference_ids"], [])

    def test_opposing_case_and_resolution_cannot_be_blank(self):
        for field in review.TEXT_FIELDS:
            a = assessment()
            a[field] = " "
            with self.subTest(field=field), self.assertRaises(UsageError):
                review.validate(a, "deep", self.d)

    def test_changed_disclosure_invalidates_review_and_preserves_history(self):
        first = review.record(self.d, "deep", assessment())
        original = (self.d / "reviews" / first).read_bytes()
        self.d.joinpath("invention-disclosure.md").write_text("A materially revised mechanism.")
        with self.assertRaisesRegex(UsageError, "Stale"):
            review.check(self.d, "deep")
        second = review.record(self.d, "deep", assessment())
        self.assertNotEqual(first, second)
        self.assertEqual((self.d / "reviews" / first).read_bytes(), original)
        review.check(self.d, "deep")

    def test_changed_art_invalidates_review(self):
        review.record(self.d, "deep", assessment())
        self.art["references"].append({"id": "R2", "verified": False})
        self.write_art()
        with self.assertRaisesRegex(UsageError, "Stale"):
            review.check(self.d, "deep")

    def test_later_search_does_not_invalidate_phase_zero(self):
        a = assessment("ready_to_search")
        a["coverage"]["search"] = "none"
        review.record(self.d, "clarify", a)
        self.art["references"].clear()
        self.write_art()
        review.check(self.d, "clarify")

    def test_other_purposes_do_not_become_patentability_findings(self):
        a = assessment("assessed_risks")
        a["purpose"] = "fto"
        review.record(self.d, "deep", a)
        a["outcome"] = "likely_patentable"
        with self.assertRaises(UsageError):
            review.validate(a, "deep", self.d)

    def test_index_cannot_escape_matter(self):
        review.record(self.d, "deep", assessment())
        (self.d / "reviews/index.json").write_text('{"deep": "../outside.json"}')
        with self.assertRaises(UsageError):
            review.check(self.d, "deep")

    def test_missing_review_inputs_are_not_silently_hashed(self):
        self.d.joinpath("invention-disclosure.md").unlink()
        with self.assertRaisesRegex(UsageError, "Missing review input"):
            review.record(self.d, "deep", assessment())


class PackageReviewTest(unittest.TestCase):
    def setUp(self):
        from test_draft_package import make_matter
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(make_matter(self.tmp.name))

    def test_missing_assessment_blocks_package(self):
        import check_package
        (self.d / "reviews/index.json").unlink()
        result = check_package.run({"dir": str(self.d), "no_audit": True})
        self.assertFalse(result["summary"]["ready_to_export"])
        self.assertIn("ASSESSMENT", [x["code"] for x in result["findings"] if x["level"] == "BLOCK"])

    def test_changed_claim_blocks_even_if_artifact_hashes_refreshed(self):
        import check_package
        import state
        with (self.d / "draft/claims.md").open("a") as handle:
            handle.write("\n19. The system of claim 8, wherein the helmet is a bicycle helmet.\n")
        state.run({"command": "hash", "dir": str(self.d), "no_audit": True})
        result = check_package.run({"dir": str(self.d), "no_audit": True})
        self.assertIn("ASSESSMENT", [x["code"] for x in result["findings"] if x["level"] == "BLOCK"])

    def test_computed_totals_do_not_invalidate_draft_review(self):
        path = self.d / "draft/filing.json"
        filing = json.loads(path.read_text())
        filing.update(total_fee=123, spec_pages=7, drawing_sheets=4)
        path.write_text(json.dumps(filing))
        review.check(self.d, "draft")
        filing["title"] = "Different technical subject"
        path.write_text(json.dumps(filing))
        with self.assertRaisesRegex(UsageError, "Stale"):
            review.check(self.d, "draft")

    def test_unresolved_draft_requires_actual_proceed_basis(self):
        a = assessment()
        a.pop("proceed_basis")
        with self.assertRaises(UsageError):
            review.record(self.d, "draft", a)


if __name__ == "__main__":
    unittest.main()
