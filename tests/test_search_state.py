"""Offline tests for scripts/state.py and scripts/_dates.py (bar math, holidays, set validation, stale)."""

import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import state  # noqa: E402
from _dates import add_months, federal_holidays, is_federal_holiday, roll_forward  # noqa: E402
from state import UsageError, compute_bar, read_json  # noqa: E402

D = dt.date


class TestDates(unittest.TestCase):
    def test_add_months_clamps(self):
        self.assertEqual(add_months(D(2024, 1, 31), 1), D(2024, 2, 29))
        self.assertEqual(add_months(D(2024, 2, 29), 12), D(2025, 2, 28))
        self.assertEqual(add_months(D(2025, 3, 15), -12), D(2024, 3, 15))
        self.assertEqual(add_months("2026-11-30", 3), D(2027, 2, 28))

    def test_holidays_2026(self):
        h = federal_holidays(2026)
        expect = [D(2026, 1, 1), D(2026, 1, 19), D(2026, 2, 16), D(2026, 5, 25), D(2026, 6, 19), D(2026, 7, 3),
                  D(2026, 9, 7), D(2026, 10, 12), D(2026, 11, 11), D(2026, 11, 26), D(2026, 12, 25)]
        self.assertEqual(sorted(h), expect)  # July 4 2026 is a Saturday -> observed Friday July 3

    def test_observance_rules(self):
        self.assertTrue(is_federal_holiday(D(2027, 7, 5)))     # Jul 4 2027 Sunday -> Monday
        self.assertTrue(is_federal_holiday(D(2027, 12, 31)))   # Jan 1 2028 Saturday -> Fri Dec 31 2027
        self.assertNotIn(D(2028, 1, 1), federal_holidays(2028))
        self.assertTrue(is_federal_holiday(D(2029, 1, 15)))    # MLK 2029
        self.assertFalse(is_federal_holiday(D(2020, 6, 19)))   # Juneteenth starts 2021

    def test_roll_forward(self):
        self.assertEqual(roll_forward(D(2026, 11, 26)), D(2026, 11, 27))   # Thanksgiving -> Friday
        self.assertEqual(roll_forward(D(2026, 7, 4)), D(2026, 7, 6))       # Saturday -> Monday (Jul 3 was observed)
        self.assertEqual(roll_forward(D(2027, 7, 4)), D(2027, 7, 6))       # Sunday -> Mon is holiday -> Tue
        self.assertEqual(roll_forward(D(2026, 11, 18)), D(2026, 11, 18))


class TestBar(unittest.TestCase):
    def test_no_disclosure(self):
        b = compute_bar({"disclosures_confirmed": "none"}, "2026-11-18")
        self.assertEqual((b["us_status"], b["foreign_status"], b["us_last_day"]), ("clear", "intact", None))

    def test_unanswered_bar_questions_stay_unknown(self):
        # F10: "never asked" must not read as "clear"
        for dates in ({}, {"conception": "2026-09-15"}, {"disclosures_confirmed": None},
                      {"disclosures_confirmed": "yes"}):
            b = compute_bar(dates, "2026-11-18")
            self.assertEqual((b["us_status"], b["foreign_status"]), ("unknown", "unknown"), dates)
        b = compute_bar({"disclosures_confirmed": "none", "earliest_public_use": "2026-01-05"}, "2026-11-18")
        self.assertEqual(b["us_status"], "clock_running")  # a recorded date wins, with a note
        self.assertTrue(any("disclosures_confirmed is 'none'" in n for n in b["notes"]))

    def test_clock_running_with_holiday_roll(self):
        b = compute_bar({"earliest_public_disclosure": "2025-11-26"}, "2026-11-18")
        self.assertEqual(b["us_status"], "clock_running")
        self.assertEqual(b["us_last_day"], "2026-11-27")   # 2026-11-26 is Thanksgiving
        self.assertEqual(b["days_left"], 9)
        self.assertEqual(b["foreign_status"], "likely_lost")
        self.assertTrue(any("Thanksgiving" in n for n in b["notes"]))

    def test_weekend_roll(self):
        b = compute_bar({"earliest_sale_or_offer": "2026-03-07"}, "2026-11-18")  # 2027-03-07 is a Sunday
        self.assertEqual(b["us_last_day"], "2027-03-08")
        self.assertEqual(b["foreign_status"], "at_risk")    # offer only

    def test_likely_barred(self):
        b = compute_bar({"earliest_public_use": "2025-06-01"}, "2026-11-18")
        self.assertEqual(b["us_status"], "likely_barred")

    def test_earliest_trigger_wins(self):
        b = compute_bar({"earliest_public_disclosure": "2026-05-01", "earliest_sale_or_offer": "2026-02-02"},
                        "2026-11-18")
        self.assertEqual(b["trigger"]["field"], "earliest_sale_or_offer")
        self.assertEqual(b["us_last_day"], "2027-02-02")

    def test_filed_within_grace(self):
        b = compute_bar({"earliest_public_disclosure": "2026-01-10", "provisional_filed": "2026-06-01"}, "2026-11-18")
        self.assertEqual(b["us_status"], "clear")
        self.assertEqual(b["foreign_status"], "likely_lost")
        b = compute_bar({"earliest_public_disclosure": "2026-07-10", "provisional_filed": "2026-06-01"}, "2026-11-18")
        self.assertEqual((b["us_status"], b["foreign_status"]), ("clear", "intact"))
        b = compute_bar({"earliest_public_disclosure": "2024-01-10", "nonprovisional_filed": "2025-06-01"}, "2026-11-18")
        self.assertEqual(b["us_status"], "likely_barred")


class TestStateCommands(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        state.run({"command": "init", "dir": self.d, "title": "Helmet signal", "today": "2026-11-18"})

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_init_layout(self):
        for sub in ("cache", "charts", "reports", "draft/out", "prosecution"):
            self.assertTrue(os.path.isdir(os.path.join(self.d, sub)))
        st = read_json(os.path.join(self.d, "state.json"))
        self.assertEqual(st["schema"], "patentassist/state@1")
        self.assertEqual(st["phase"], "setup")
        pa = read_json(os.path.join(self.d, "prior-art.json"))
        self.assertEqual(pa["schema"], "patentassist/prior-art@1")
        with self.assertRaises(UsageError):
            state.run({"command": "init", "dir": self.d, "title": "again"})

    def test_set_validation_and_bar_recompute(self):
        state.run({"command": "set", "dir": self.d, "path": "phase", "value": "lite", "no_audit": True})
        with self.assertRaises(UsageError):
            state.run({"command": "set", "dir": self.d, "path": "phase", "value": "bogus", "no_audit": True})
        with self.assertRaises(UsageError):
            state.run({"command": "set", "dir": self.d, "path": "dates.conception", "value": '"11/18/2026"'})
        with self.assertRaises(UsageError):
            state.run({"command": "set", "dir": self.d, "path": "bar.us_status", "value": '"clear"'})
        for outlook in ("Likely patentable within the reviewed scope", "Likely unpatentable as formulated"):
            state.run({"command": "set", "dir": self.d, "path": "phases.deep.outlook", "value": outlook})
            self.assertEqual(read_json(os.path.join(self.d, "state.json"))["phases"]["deep"]["outlook"], outlook)
        r = state.run({"command": "set", "dir": self.d, "path": "dates.earliest_public_disclosure",
                       "value": '"2025-11-26"', "today": "2026-11-18", "no_audit": True})
        self.assertEqual(r["bar"]["us_last_day"], "2026-11-27")
        st = read_json(os.path.join(self.d, "state.json"))
        self.assertEqual(st["bar"]["us_status"], "clock_running")
        state.run({"command": "set", "dir": self.d, "path": "open_questions", "value": "Inventor 2 address",
                   "append": True, "no_audit": True})
        st = read_json(os.path.join(self.d, "state.json"))
        self.assertEqual(st["open_questions"], ["Inventor 2 address"])

    def test_decide_and_log_audit(self):
        state.run({"command": "decide", "dir": self.d, "gate": "lite", "choice": "run deep search"})
        state.run({"command": "log", "dir": self.d, "kind": "note", "json_detail": '{"text": "hello"}'})
        st = read_json(os.path.join(self.d, "state.json"))
        self.assertEqual(st["decisions"][-1]["choice"], "run deep search")
        with open(os.path.join(self.d, "audit.jsonl"), encoding="utf-8") as fh:
            kinds = [json.loads(x)["kind"] for x in fh if x.strip()]
        self.assertIn("gate", kinds)
        self.assertEqual(kinds[-1], "note")
        with self.assertRaises(UsageError):
            state.run({"command": "log", "dir": self.d, "kind": "bogus"})

    def _write(self, rel, text):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def test_stale_detection(self):
        self._write("draft/claims.md", "# Claims\n\n1. A helmet.\n")
        self._write("draft/figures.json", "{}")
        self._write("draft/spec.md", "## TITLE\nHelmet\n")
        state.run({"command": "hash", "dir": self.d, "paths": ["draft/spec.md"]})
        r = state.run({"command": "stale", "dir": self.d})
        self.assertEqual(r["exit_code"], 0)
        self._write("draft/claims.md", "# Claims\n\n1. A helmet comprising a shell.\n")
        r = state.run({"command": "stale", "dir": self.d})
        self.assertEqual(r["exit_code"], 1)
        self.assertEqual([s["downstream"] for s in r["stale"]], ["draft/spec.md"])
        self.assertEqual(r["stale"][0]["changed_inputs"], ["draft/claims.md"])
        state.run({"command": "hash", "dir": self.d, "paths": ["draft/spec.md"]})
        self.assertEqual(state.run({"command": "stale", "dir": self.d})["exit_code"], 0)

    def test_stale_propagates_and_mtime_fallback(self):
        self._write("invention-disclosure.md", "x")
        self._write("draft/claims.md", "1. A helmet.")
        self._write("draft/spec.md", "spec")
        self._write("draft/figures.json", "{}")
        self._write("draft/filing.json", "{}")
        self._write("draft/out/spec.docx", "built")
        state.run({"command": "hash", "dir": self.d, "paths": ["draft/claims.md", "draft/spec.md", "draft/out/"]})
        time.sleep(0.02)
        self._write("invention-disclosure.md", "changed")
        r = state.run({"command": "stale", "dir": self.d})
        downs = [s["downstream"] for s in r["stale"]]
        self.assertEqual(downs, ["draft/claims.md", "draft/spec.md", "draft/out/"])

    def test_show(self):
        r = state.run({"command": "show", "dir": self.d})
        self.assertIn("statutory-bar", r["next_gate"])
        self.assertTrue(any(line.startswith("Matter: Helmet signal") for line in r["text"]))


if __name__ == "__main__":
    unittest.main()


class TestNextGateAfterDeep(unittest.TestCase):
    """Dogfooding found the deep->draft hint unreachable: phase 'deep' with deep done still said
    'Finish the deep search'."""

    def test_deep_done_points_to_draft_gate(self):
        import state as st_mod
        st = st_mod.default_state("x", today="2026-11-18")
        st["bar"]["us_status"] = "clear"
        st["dates"]["disclosures_confirmed"] = "none"
        st["phase"] = "deep"
        st["phases"]["lite"]["status"] = "done"
        st["phases"]["deep"]["status"] = "done"
        self.assertIn("Gate deep->draft", st_mod.next_gate(st))
        st["phases"]["deep"]["status"] = "in_progress"
        self.assertIn("Finish the deep search", st_mod.next_gate(st))


class TestNextGateAfterExport(unittest.TestCase):
    def test_draft_done_points_to_filing(self):
        import state as st_mod
        st = st_mod.default_state("x", today="2026-11-18")
        st["bar"]["us_status"] = "clear"
        st["dates"]["disclosures_confirmed"] = "none"
        st["phase"] = "draft"
        for k in ("lite", "deep", "draft"):
            st["phases"][k]["status"] = "done"
        st["phases"]["draft"].update({"claims_locked": True, "figures_locked": True})
        self.assertIn("Patent Center", st_mod.next_gate(st))


class TestBarQuestionsGate(unittest.TestCase):
    """F10: setting an unrelated date must not flip the bar to clear; next_gate keeps asking."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        state.run({"command": "init", "dir": self.d, "title": "x", "today": "2026-11-18", "no_audit": True})

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_conception_date_keeps_unknown(self):
        r = state.run({"command": "set", "dir": self.d, "path": "dates.conception", "value": "2026-09-15",
                       "today": "2026-11-18", "no_audit": True})
        self.assertEqual(r["bar"]["us_status"], "unknown")
        self.assertIn("statutory-bar", state.run({"command": "show", "dir": self.d})["next_gate"])
        r = state.run({"command": "set", "dir": self.d, "path": "dates.disclosures_confirmed", "value": "none",
                       "today": "2026-11-18", "no_audit": True})
        self.assertEqual((r["bar"]["us_status"], r["bar"]["foreign_status"]), ("clear", "intact"))
        self.assertNotIn("statutory-bar", state.run({"command": "show", "dir": self.d,
                                                      "today": "2026-11-18"})["next_gate"])
        with self.assertRaises(UsageError):
            state.run({"command": "set", "dir": self.d, "path": "dates.disclosures_confirmed", "value": "maybe"})

    def test_date_without_confirmation_asks_to_confirm(self):
        state.run({"command": "set", "dir": self.d, "path": "dates.earliest_sale_or_offer", "value": '"2026-03-07"',
                   "today": "2026-11-18", "no_audit": True})
        gate = state.run({"command": "show", "dir": self.d, "today": "2026-11-18"})["next_gate"]
        self.assertIn("disclosures_confirmed yes", gate)


class TestInitConfidentiality(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_flag_and_default(self):
        r = state.run({"command": "init", "dir": self.d, "title": "x", "confidentiality": "detailed",
                       "no_audit": True})
        self.assertEqual(r["state"]["profile"]["confidentiality"], "detailed")
        self.assertTrue(any("confidentiality detailed" in t for t in r["text"]))
        r = state.run({"command": "init", "dir": self.d, "title": "x", "force": True, "no_audit": True})
        self.assertEqual(r["state"]["profile"]["confidentiality"], "abstracted")
        self.assertTrue(any("defaulted to abstracted" in t for t in r["text"]))
        with self.assertRaises(UsageError):
            state.run({"command": "init", "dir": self.d, "title": "x", "force": True, "confidentiality": "open"})

    def test_cli_flag(self):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc = state.main(["init", "--dir", self.d, "--title", "x", "--confidentiality", "detailed", "--no-audit"])
        self.assertEqual(rc, 0)
        self.assertEqual(read_json(os.path.join(self.d, "state.json"))["profile"]["confidentiality"], "detailed")


class TestCanonicalGates(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        state.run({"command": "init", "dir": self.d, "title": "x", "no_audit": True})

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_decide_validates_gate(self):
        for g in state.GATES:
            state.run({"command": "decide", "dir": self.d, "gate": g, "choice": "ok", "no_audit": True})
        with self.assertRaises(UsageError) as cm:
            state.run({"command": "decide", "dir": self.d, "gate": "lite->deep", "choice": "x", "no_audit": True})
        self.assertIn("did you mean 'lite'", str(cm.exception))
        r = state.run({"command": "decide", "dir": self.d, "gate": "client-call", "choice": "x", "force_gate": True,
                       "no_audit": True})
        self.assertEqual(r["decision"]["gate"], "client-call")
        self.assertEqual(state.GATES, ("clarify", "scope", "lite", "deep", "claims", "package", "oa-strategy", "oa-final", "mine"))


class TestFilingComputedFieldsNotStale(unittest.TestCase):
    """F15: writing total_fee / spec_pages / drawing_sheets into filing.json must not make out/ stale."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        state.run({"command": "init", "dir": self.d, "title": "x", "no_audit": True})
        for rel, obj in (("draft/claims.md", "1. A pot."), ("draft/spec.md", "spec"), ("draft/figures.json", "{}"),
                         ("draft/out/spec.docx", "built")):
            p = os.path.join(self.d, rel)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(obj)
        self.filing = os.path.join(self.d, "draft", "filing.json")
        state.write_json(self.filing, {"schema": "patentassist/filing@1", "title": "Pot", "entity_status": "micro"})
        state.run({"command": "hash", "dir": self.d, "paths": ["draft/spec.md", "draft/out/"]})

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_fee_write_back_is_not_stale_but_real_edit_is(self):
        f = read_json(self.filing)
        f.update({"total_fee": 65, "spec_pages": 13, "drawing_sheets": 4})
        time.sleep(0.02)
        state.write_json(self.filing, f)
        self.assertEqual(state.run({"command": "stale", "dir": self.d})["exit_code"], 0)
        f["entity_status"] = "small"
        state.write_json(self.filing, f)
        r = state.run({"command": "stale", "dir": self.d})
        self.assertEqual([s["downstream"] for s in r["stale"]], ["draft/out/"])

    def test_old_raw_hash_still_matches_unchanged_file(self):
        p = os.path.join(self.d, "state.json")
        st = read_json(p)
        st["artifacts"]["draft/out/"]["inputs"]["draft/filing.json"] = state.sha256_path(self.filing)
        state.write_json(p, st)
        self.assertEqual(state.run({"command": "stale", "dir": self.d})["exit_code"], 0)

    def test_non_json_filing_falls_back_to_bytes(self):
        with open(self.filing, "w", encoding="utf-8") as fh:
            fh.write("not json")
        self.assertEqual(state.sha256_filing(self.filing), state.sha256_path(self.filing))
