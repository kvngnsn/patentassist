"""Offline tests for scripts/check_claims.py (seeded-error fixtures in tests/fixtures/draft/)."""

import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
FIX = os.path.join(HERE, "fixtures", "draft")
sys.path.insert(0, SCRIPTS)

import check_claims as cc  # noqa: E402


def run_file(name, **kw):
    args = {"claims": os.path.join(FIX, name), "no_audit": True, "dir": os.path.join(FIX, "no-such-dir")}
    args.update(kw)
    return cc.run(args)


def run_text(text, **kw):
    args = {"text": text, "no_audit": True, "dir": os.path.join(FIX, "no-such-dir")}
    args.update(kw)
    return cc.run(args)


def codes(res, level=None):
    return [(f["code"], f["where"]) for f in res["findings"] if level is None or f["level"] == level]


def blocks(res):
    return [f for f in res["findings"] if f["level"] == "BLOCK"]


class TestParser(unittest.TestCase):
    def test_dependency_phrases(self):
        text = """1. A widget comprising a body.
2. The widget of claim 1, wherein the body is red.
3. The widget according to claim 2, wherein the body is round.
4. The widget as claimed in claim 1, wherein the body is hollow.
5. The widget of any one of claims 1-3, wherein the body is metal.
6. The widget of claim 1 or 2, wherein the body is plastic.
7. (Canceled)
8. (Withdrawn) The widget of claim 1, wherein the body is glass.
9. The widget as in any of the preceding claims, wherein the body is wood.
"""
        claims = {c["num"]: c for c in cc.parse_claims(text)}
        self.assertEqual(claims[1]["dep_kind"], "independent")
        self.assertEqual(claims[2]["deps"], [1])
        self.assertEqual(claims[3]["deps"], [2])
        self.assertEqual(claims[4]["deps"], [1])
        self.assertEqual(claims[5]["deps"], [1, 2, 3])
        self.assertEqual(claims[5]["dep_kind"], "multiple")
        self.assertEqual(claims[6]["deps"], [1, 2])
        self.assertEqual(claims[7]["dep_kind"], "canceled")
        self.assertEqual(claims[8]["status"], "withdrawn")
        self.assertEqual(claims[9]["dep_kind"], "multiple")
        self.assertNotIn(7, claims[9]["deps"])

    def test_wrapped_lines_and_sub_elements(self):
        text = "# Claims\n\n1. A helmet comprising:\n   a shell;\n   a light mounted\n   on the shell.\n\n2. The helmet of claim 1.\n"
        claims = cc.parse_claims(text)
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0]["text"], "A helmet comprising: a shell; a light mounted on the shell.")

    def test_range_canceled(self):
        claims = cc.parse_claims("1-3. (Canceled)\n4. A widget.\n")
        self.assertEqual([c["num"] for c in claims], [1, 2, 3, 4])
        self.assertTrue(all(c["dep_kind"] == "canceled" for c in claims[:3]))

    def test_lemma(self):
        for pl, sg in [("sensors", "sensor"), ("bodies", "body"), ("media", "medium"), ("lenses", "lens"),
                       ("processes", "process"), ("caches", "cache"), ("data", "data"), ("apparatus", "apparatus"),
                       ("switches", "switch"), ("cases", "case")]:
            self.assertEqual(cc.lemma(pl), sg, pl)


class TestCleanSets(unittest.TestCase):
    def test_clean_set_no_blocks_few_warns(self):
        res = run_file("clean_claims.md", spec=os.path.join(FIX, "clean_spec.md"), entity="small")
        self.assertEqual(blocks(res), [], res["findings"])
        self.assertLessEqual(res["summary"]["warnings"], 2, res["findings"])
        self.assertEqual(res["exit_code"], 0)
        c = res["summary"]["counts"]
        self.assertGreaterEqual(c["active"], 15)
        self.assertEqual(c["independent"], 3)
        self.assertEqual(c["excess_total"], 0)
        self.assertEqual(sorted(res["summary"]["categories"]), ["crm", "method", "system/apparatus"])
        self.assertIn("TERM_SUPPORT", res["checks_run"])

    def test_tricky_valid_set_no_false_blocks(self):
        # plurality / at least one / one or more, ordinal coordination, Markush group, inherent "a thickness of",
        # "the same", "the top and bottom surfaces", gerund step reference, verbs after nouns
        res = run_file("tricky_valid_claims.md")
        self.assertEqual(blocks(res), [], res["findings"])
        self.assertLessEqual(res["summary"]["warnings"], 2, res["findings"])

    def test_tree_and_terms(self):
        res = run_file("clean_claims.md")
        tree = "\n".join(res["tree"])
        self.assertIn("1 (independent, method)", tree)
        self.assertIn("15 (independent, crm)", tree)
        self.assertIn("non-transitory computer-readable medium", res["terms"]["15"]["introduces"])
        self.assertIn("first light", res["terms"]["4"]["refers"])


class TestBrokenSets(unittest.TestCase):
    def test_missing_antecedent(self):
        res = run_file("broken_antecedent.md")
        msgs = {(f["where"], f["level"]): f["message"] for f in res["findings"] if f["code"] == "ANTECEDENT"}
        self.assertIn(("claim 2", "BLOCK"), msgs)
        self.assertIn('"the battery"', msgs[("claim 2", "BLOCK")])
        self.assertIn("a battery", msgs[("claim 2", "BLOCK")])
        self.assertIn("claim 3", msgs[("claim 4", "BLOCK")])  # introduced outside the chain
        self.assertIn("before it is introduced", msgs[("claim 5", "BLOCK")])
        self.assertIn(("claim 7", "WARN"), msgs)  # plural vs singular
        self.assertIn(("DOUBLE_INTRO", "claim 6"), codes(res, "WARN"))
        self.assertEqual(res["exit_code"], 1)

    def test_forward_and_missing_dependency(self):
        res = run_file("broken_forward.md")
        got = codes(res, "BLOCK")
        self.assertIn(("DEP_FORWARD", "claim 2"), got)
        self.assertIn(("DEP_MISSING", "claim 5"), got)
        self.assertIn(("DEP_FORWARD", "claim 6"), got)
        self.assertIn(("CLAIM_NUMBERING", "claim 8"), got)
        # no cascade of antecedent blocks on claims whose dependency is already broken
        self.assertFalse([f for f in blocks(res) if f["code"] == "ANTECEDENT"])

    def test_multiple_on_multiple(self):
        res = run_file("broken_multi.md")
        got = codes(res, "BLOCK")
        self.assertIn(("MULTI_ON_MULTI", "claim 4"), got)
        self.assertIn(("MULTI_ON_MULTI", "claim 6"), got)  # indirect, through claim 5
        self.assertIn(("MULTI_DEP_FORM", "claim 7"), got)
        self.assertIn(("MULTI_DEP", "claim 3"), codes(res, "WARN"))
        c = res["summary"]["counts"]
        self.assertEqual(c["multiple_dependent"], [3, 4, 6, 7])
        # 1 + 1 + 2 (claim 3) + 3 (claim 4) + 2 (claim 5 depends from multiple claim 3) + 2 + 2 = 13
        self.assertEqual(c["total_for_fees"], 13)

    def test_two_sentences_and_period(self):
        res = run_file("broken_sentence.md")
        got = codes(res, "BLOCK")
        self.assertIn(("ONE_SENTENCE", "claim 1"), got)
        self.assertIn(("ONE_SENTENCE", "claim 2"), got)
        self.assertNotIn(("ONE_SENTENCE", "claim 3"), got)  # FIG., ft., e.g. are abbreviations
        self.assertFalse([f for f in res["findings"] if f["code"] == "INDEFINITE" and '"The"' in f["message"]])

    def test_nonce(self):
        res = run_file("broken_nonce.md")
        warns = [f["message"] for f in res["findings"] if f["code"] == "NONCE_112F"]
        self.assertTrue(any("processing module configured to" in m and "Williamson" in m for m in warns))
        self.assertTrue(any(m.startswith('"means for"') for m in warns))
        self.assertTrue(any("circuit" in m and "lower risk" in m for m in warns))
        self.assertEqual(blocks(res), [])

    def test_nonce_ignores_claim_subject(self):
        res = run_text("1. A system for signaling, the system comprising a processor configured to blink a light.\n")
        self.assertFalse([f for f in res["findings"] if f["code"] == "NONCE_112F"])

    def test_indefinite(self):
        res = run_file("broken_indefinite.md")
        msgs = " ".join(f["message"] for f in res["findings"] if f["code"] == "INDEFINITE")
        for word in ("substantially", "may", "such as", "and/or", "Bluetooth", "WiFi"):
            self.assertIn(word, msgs)
        self.assertEqual(blocks(res), [])

    def test_about_only_with_number(self):
        res = run_text("1. A wheel rotatable about an axis and having a diameter of about 5 cm.\n")
        msgs = [f["message"] for f in res["findings"] if f["code"] == "INDEFINITE"]
        self.assertEqual(len([m for m in msgs if m.startswith('"about')]), 1)


class TestAntecedentUnits(unittest.TestCase):
    def ante(self, text, level=None):
        res = run_text(text)
        return [f for f in res["findings"] if f["code"] == "ANTECEDENT" and (level is None or f["level"] == level)]

    def test_plurality_and_each(self):
        t = ("1. A device comprising a plurality of sensors, wherein each sensor is coupled to a bus, and the sensors "
             "are spaced apart.\n")
        self.assertEqual(self.ante(t), [])

    def test_singular_ref_to_plurality_warns(self):
        t = "1. A device comprising a plurality of sensors, wherein the sensor is coupled to a bus.\n"
        f = self.ante(t)
        self.assertEqual([x["level"] for x in f], ["WARN"])

    def test_ordinals_are_distinct(self):
        t = "1. A device comprising a first light, wherein the second light is red.\n"
        f = self.ante(t)
        self.assertTrue(f and f[0]["level"] in ("BLOCK", "WARN"))
        self.assertIn("second light", f[0]["message"])

    def test_at_least_one(self):
        t = "1. A device comprising at least one processor, wherein the at least one processor is a microcontroller.\n"
        self.assertEqual(self.ante(t), [])

    def test_longest_match_multiword(self):
        t = ("1. A device comprising a temperature sensor and a pressure sensor, wherein the temperature sensor is "
             "above the pressure sensor.\n")
        self.assertEqual(self.ante(t), [])
        t2 = "1. A device comprising a temperature sensor and a pressure sensor, wherein the sensor is red.\n"
        f = self.ante(t2, "WARN")
        self.assertTrue(f and "more than one" in f[0]["message"])

    def test_short_form_reference(self):
        t = "1. A device comprising a temperature sensor, wherein the sensor is red.\n"
        self.assertEqual(self.ante(t), [])

    def test_dependent_category_mismatch(self):
        t = "1. A method comprising heating a fluid.\n2. The system of claim 1, wherein the fluid is water.\n"
        f = self.ante(t, "BLOCK")
        self.assertTrue(f and 'The system' in f[0]["message"])

    def test_multiple_dependent_branch(self):
        t = ("1. A device comprising a body.\n2. The device of claim 1, further comprising a lid.\n"
             "3. The device of claim 1 or 2, wherein the lid is clear.\n")
        f = self.ante(t, "WARN")
        self.assertTrue(f and "claim 1" in f[0]["message"])


class TestCountsAndCli(unittest.TestCase):
    def test_excess_counts_and_fee_table(self):
        lines = ["%d. A widget number %d comprising a body." % (i, i) for i in range(1, 5)]
        lines += ["%d. The widget of claim 1, wherein the body is red." % i for i in range(5, 23)]
        res = run_text("\n".join(lines) + "\n", entity="small")
        c = res["summary"]["counts"]
        self.assertEqual(c["independent"], 4)
        self.assertEqual(c["excess_independent"], 1)
        self.assertEqual(c["total_for_fees"], 22)
        self.assertEqual(c["excess_total"], 2)
        fees = res["summary"]["fees"]
        if os.path.exists(cc.FEES_MD) and cc.load_fee_table():
            self.assertTrue(fees and fees["total"] > 0)

    def test_cli_exit_codes(self):
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_claims.py"),
                            os.path.join(FIX, "clean_claims.md"), "--no-audit", "--json",
                            "--dir", os.path.join(FIX, "no-such-dir")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('"findings"', p.stdout)
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_claims.py"),
                            os.path.join(FIX, "broken_forward.md"), "--no-audit",
                            "--dir", os.path.join(FIX, "no-such-dir")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("Dependency tree:", p.stdout)
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_claims.py"), "/no/such/file.md",
                            "--no-audit"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()


class TestTrademarkRuns(unittest.TestCase):
    """Dogfooding: "Bluetooth Low Energy" produced three separate trademark warnings."""

    def test_capitalized_run_is_one_finding(self):
        res = run_text("# Claims\n\n1. A device comprising a Bluetooth Low Energy transceiver.\n")
        msgs = [f["message"] for f in res["findings"] if f["code"] == "INDEFINITE"]
        self.assertEqual(len(msgs), 1)
        self.assertIn('"Bluetooth Low Energy"', msgs[0])


class TestVerbsEndNounPhrases(unittest.TestCase):
    """Dogfooding (F29): "whose fingerprint matches the spectrum" was parsed as the term
    "fingerprint matches"; "an initial heating period" split into "initial" + "period"; and
    "each X comprising a Y" then "a Y" gave DOUBLE_INTRO."""

    def terms(self, text):
        return cc.run({"text": text, "no_audit": True, "dir": os.path.join(FIX, "no-such-dir")})

    def test_third_person_verbs_end_the_phrase(self):
        res = self.terms("1. A device comprising a memory storing a profile having a baseline fingerprint, and a "
                         "controller that computes a measured fingerprint and selects the profile when the baseline "
                         "fingerprint matches the measured fingerprint.\n"
                         "2. The device of claim 1, wherein the controller stores a new profile when the measured "
                         "fingerprint matches none of the stored fingerprints.\n")
        self.assertEqual([f for f in res["findings"] if f["level"] in ("BLOCK", "WARN")], [], res["findings"])
        self.assertIn("baseline fingerprint", res["terms"]["1"]["refers"])
        self.assertNotIn("baseline fingerprint matches", res["terms"]["1"]["refers"])
        self.assertIn("measured fingerprint", res["terms"]["2"]["refers"])

    def test_ambiguous_verbs_need_an_object(self):
        ch = cc.chunk("the controller signals a fault and the control signals are logged")
        texts = [c["text"] for c in ch]
        self.assertIn("controller", texts)
        self.assertIn("control signals", texts)   # plural noun before a verb stays a noun
        self.assertNotIn("controller signals", texts)

    def test_gerund_modifier_inside_phrase(self):
        ch = cc.chunk("during an initial heating period, a sensor detecting vibration")
        texts = [c["text"] for c in ch]
        self.assertIn("initial heating period", texts)
        self.assertIn("sensor", texts)
        self.assertNotIn("sensor detecting vibration", texts)

    def test_each_x_comprising_a_y_is_distributive(self):
        res = self.terms("1. A system comprising: a memory storing a plurality of profiles, each profile comprising "
                         "a fingerprint; and a controller configured to store a new profile comprising a fingerprint.\n"
                         "2. The system of claim 1, further comprising a sensor, wherein each sensor reading has a "
                         "timestamp.\n")
        self.assertFalse([f for f in res["findings"] if f["code"] == "DOUBLE_INTRO"], res["findings"])

    def test_planted_double_intro_still_caught(self):
        res = self.terms("1. A device comprising a lens and a lens, wherein the lens is clear.\n")
        self.assertTrue([f for f in res["findings"] if f["code"] == "DOUBLE_INTRO"])
