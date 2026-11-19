"""Offline tests for scripts/check_spec.py."""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FIX = os.path.join(HERE, "fixtures", "draft")
sys.path.insert(0, SCRIPTS)

import check_spec as cs  # noqa: E402

NODIR = os.path.join(FIX, "no-such-dir")


def run(spec, **kw):
    args = {"spec": os.path.join(FIX, spec) if not os.path.isabs(spec) else spec,
            "figures": os.path.join(FIX, "clean_figures.json"),
            "filing": os.path.join(HERE, "fixtures", "build", "filing.json"), "type": "nonprovisional",
            "no_audit": True, "dir": NODIR}
    args.update(kw)
    return cs.run(args)


def by_code(res, code, level=None):
    return [f for f in res["findings"] if f["code"] == code and (level is None or f["level"] == level)]


class TestCleanSpec(unittest.TestCase):
    def test_clean_spec_passes(self):
        res = run("clean_spec.md", claims=os.path.join(FIX, "clean_claims.md"))
        self.assertEqual([f for f in res["findings"] if f["level"] == "BLOCK"], [], res["findings"])
        self.assertEqual(res["summary"]["warnings"], 0, res["findings"])
        self.assertEqual(res["exit_code"], 0)
        for c in ("SECTION_ORDER", "TITLE_LEN", "ABSTRACT", "FIG_COVERAGE", "NUMERALS", "RISKY_WORDS", "FUNDING",
                  "INCORP_BY_REF", "CLAIM_SUPPORT"):
            self.assertIn(c, res["checks_run"])
        self.assertIn("102", res["summary"]["numerals"])
        self.assertIn("212", res["summary"]["numerals"])


class TestBrokenSpec(unittest.TestCase):
    def setUp(self):
        self.res = run("broken_spec.md")

    def test_abstract_over_150(self):
        f = by_code(self.res, "ABSTRACT", "BLOCK")
        self.assertTrue(f and "150" in f[0]["message"])

    def test_numeral_two_names(self):
        f = by_code(self.res, "NUMERALS", "BLOCK")
        self.assertTrue(any("102" in x["message"] and "chin strap" in x["message"] for x in f), f)

    def test_fig3_missing_from_brief(self):
        f = by_code(self.res, "FIG_COVERAGE", "BLOCK")
        self.assertTrue(any(x["where"] == "FIG. 3" and "Brief Description" in x["message"] for x in f))

    def test_present_invention(self):
        f = by_code(self.res, "RISKY_WORDS", "WARN")
        self.assertTrue(any("present invention" in x["message"] for x in f))

    def test_exit_code(self):
        self.assertEqual(self.res["exit_code"], 1)


class TestUnits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, text, name="spec.md"):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def test_fig_expansion(self):
        got = [f for f, _ in cs.figs_in("See FIGS. 2A-2C and FIG. 4, and FIGS. 5 and 6, Figure 7.")]
        self.assertEqual(got, ["FIG. 2A", "FIG. 2B", "FIG. 2C", "FIG. 4", "FIG. 5", "FIG. 6", "FIG. 7"])

    def test_numerals_skip_units_and_years(self):
        got = cs.numerals_in("The shell 102 is 25 mm thick, filed in 2019, per U.S. Pat. No. 9,457,709, "
                             "about 100 meters from lights 104a, rated at 60 seconds.", lambda p: 1)
        nums = [n for n, _k, _d, _l in got]
        self.assertEqual(nums, ["102", "104a"])

    def test_section_order_and_missing(self):
        p = self.write("## TITLE\n\nWidget\n\n## SUMMARY\n\nA widget.\n\n## BACKGROUND\n\nOld widgets.\n")
        res = run(p, figures=None, filing=None, type="nonprovisional")
        got = {(f["code"], f["level"]) for f in res["findings"]}
        self.assertIn(("SECTION_ORDER", "WARN"), got)  # background after summary
        msgs = " ".join(f["message"] for f in res["findings"] if f["level"] == "BLOCK")
        self.assertIn("DETAILED DESCRIPTION", msgs)
        self.assertIn("ABSTRACT", msgs)
        self.assertIn("claim", msgs)

    def test_title_and_abstract_limits(self):
        title = " ".join(["word"] * 120)
        p = self.write("## TITLE\n\n%s\n\n## DETAILED DESCRIPTION\n\nA widget 10 has a body.\n\n## CLAIMS\n\n"
                       "1. A widget.\n\n## ABSTRACT\n\nA widget said to have means.\n" % title)
        res = run(p, figures=None, filing=None)
        self.assertTrue(by_code(res, "TITLE_LEN", "BLOCK"))
        a = by_code(res, "ABSTRACT", "WARN")
        msgs = " ".join(x["message"] for x in a)
        self.assertIn("said", msgs)
        self.assertIn("means", msgs)
        self.assertIn("50-150", msgs)

    def test_funding_required(self):
        p = self.write("## TITLE\n\nWidget\n\n## DETAILED DESCRIPTION\n\nA widget.\n\n## CLAIMS\n\n1. A widget.\n\n"
                       "## ABSTRACT\n\n" + "word " * 60 + "\n")
        fil = self.write('{"schema": "patentassist/filing@1", "title": "Widget", '
                         '"government_interest": "NSF grant 1234567"}', "filing.json")
        res = run(p, figures=None, filing=fil)
        self.assertTrue(by_code(res, "FUNDING", "BLOCK"))

    def test_incorporation_by_reference(self):
        p = self.write("## TITLE\n\nWidget\n\n## DETAILED DESCRIPTION\n\nU.S. Pat. No. 9,457,709 is incorporated "
                       "herein by reference. The article \"Widgets in Practice\" in the Journal of Widgets is "
                       "incorporated by reference in its entirety.\n\nWO 2020/123456 is incorporated by reference."
                       "\n\n## CLAIMS\n\n1. A widget.\n\n## ABSTRACT\n\n" + "word " * 60 + "\n")
        res = run(p, figures=None, filing=None)
        self.assertEqual(len(by_code(res, "INCORP_BY_REF", "WARN")), 2)

    def test_provisional_thin(self):
        p = self.write("## TITLE\n\nWidget\n\n## DETAILED DESCRIPTION\n\nA widget has a body.\n")
        res = run(p, figures=None, filing=None, type="provisional")
        f = by_code(res, "PROVISIONAL_THIN", "WARN")
        self.assertTrue(f and "New Railhead" in f[0]["message"])
        self.assertFalse([x for x in res["findings"] if x["level"] == "BLOCK" and "ABSTRACT" in x["message"]])

    def test_numerals_vs_figures_json(self):
        p = self.write("## TITLE\n\nWidget\n\n## BRIEF DESCRIPTION OF THE DRAWINGS\n\nFIG. 1 is a view.\n\n"
                       "## DETAILED DESCRIPTION\n\nFIG. 1 shows a widget 10 with a body 12 and a lid 14.\n\n"
                       "## CLAIMS\n\n1. A widget.\n\n## ABSTRACT\n\n" + "word " * 60 + "\n")
        fj = self.write('{"schema": "patentassist/figures@1", "figures": [{"id": "FIG. 1", "type": "block", '
                        '"nodes": [{"id": "a", "label": "Widget", "numeral": 10}, {"id": "b", "label": "Body", '
                        '"numeral": 12}, {"id": "c", "label": "Hinge", "numeral": 16}]}]}', "figures.json")
        res = run(p, figures=fj, filing=None)
        msgs = " ".join(f["message"] for f in by_code(res, "NUMERALS", "BLOCK"))
        self.assertIn("numeral 16 appears in figures.json", msgs)
        self.assertIn("numeral 14", msgs)


if __name__ == "__main__":
    unittest.main()


class TestDogfoodFalsePositives(unittest.TestCase):
    """Found dogfooding a historical synthetic drafting exercise: the skill's own boilerplate and flowchart wording warned."""

    SPEC = ("# Specification\n\n## TITLE\n\nWidget\n\n## BACKGROUND\n\nWidgets exist.\n\n## SUMMARY\n\n"
            "A widget.\n\n## BRIEF DESCRIPTION OF THE DRAWINGS\n\nFIG. 1 is a flowchart.\n\n"
            "## DETAILED DESCRIPTION\n\nThe figures are not necessarily to scale. Referring to FIG. 1, at step 102 "
            "a controller 110 reads a sensor 120. At decision 104 the controller 110 compares. At decision 106 "
            "the controller 110 stops.\n\n## ABSTRACT\n\n" + "A widget reads a sensor and compares values. " * 8 + "\n")

    def _run(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        path = os.path.join(d, "spec.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.SPEC)
        return cs.run({"spec": path, "no_audit": True, "dir": os.path.join(d, "no-such-dir"), "type": "provisional"})

    def test_not_necessarily_to_scale_is_not_risky(self):
        res = self._run()
        self.assertFalse([f for f in res["findings"] if f["code"] == "RISKY_WORDS" and "necessar" in f["message"]])

    def test_decision_word_is_generic(self):
        res = self._run()
        self.assertFalse([f for f in res["findings"] if f["code"] == "NUMERALS" and '"decision"' in f["message"]])


class TestSharedSpecParser(unittest.TestCase):
    """F04: check_spec.py and check_drawings.py parsed sections and numerals separately and drifted
    apart. Both now use scripts/_specparse.py."""

    def test_both_scripts_use_one_parser(self):
        import _specparse
        import check_drawings
        self.assertIs(cs.GENERIC_NAMES, _specparse.GENERIC_NAMES)
        self.assertIs(check_drawings.GENERIC_NAMES, _specparse.GENERIC_NAMES)
        self.assertIn("decision", _specparse.GENERIC_NAMES)
        self.assertIn("the", _specparse.STOP_BEFORE)

    def test_same_numerals_from_both(self):
        import check_drawings
        text = ("The shell 102 and the strap 104, 106 attach. At decision 312 the controller 110 checks whether "
                "14 of the 16 trials passed, about 3.7 V, per claim 12 and FIG. 22, U.S. Pat. No. 9,457,709.")
        a = sorted(set(n for n, _k, _d, _l in cs.numerals_in(text, lambda p: 1)))
        b = sorted(check_drawings.spec_numerals(text))
        self.assertEqual(a, b)
        self.assertEqual(a, ["102", "104", "106", "110", "312"])

    def test_sub_headings_and_fig_refs(self):
        import check_drawings
        md = "## BRIEF DESCRIPTION OF THE DRAWINGS\n\nFIGS. 1-2 show it.\n\n## DETAILED DESCRIPTION\n\n### Overview\n\n" \
             "Referring to FIG. 1 and FIG. 2A, a pad 120.\n\n## ABSTRACT\n\nX.\n"
        spec = cs.parse_spec(md)
        self.assertEqual([s["key"] for s in spec["sections"]], ["BRIEF_DRAWINGS", "DETAILED_DESCRIPTION", "ABSTRACT"])
        self.assertEqual([f for f, _ in cs.figs_in(cs.body_text(cs.section(spec, "DETAILED_DESCRIPTION")))],
                         ["FIG. 1", "FIG. 2A"])
        self.assertEqual(check_drawings.fig_refs("FIGS. 1-2 show it, and FIG. 1 to the left"), {"1", "2"})
