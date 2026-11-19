"""Offline tests for scripts/deadlines.py: weekend/holiday roll, extensions from the unrolled date,
maintenance windows, Feb 29 provisional, the yaml rule parser, and the portfolio docket."""

import contextlib
import datetime as dt
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import deadlines  # noqa: E402
import fees  # noqa: E402
from state import UsageError  # noqa: E402

D = dt.date


def oa(mailed, typ, **kw):
    kw.update({"command": "oa", "mailed": mailed, "type": typ, "today": kw.get("today", "2026-01-01")})
    return deadlines.run(kw)["deadline"]


class TestMiniYaml(unittest.TestCase):
    def test_parser_shapes(self):
        y = ('top:\n  a: "x # not a comment"\n  b: [1, two, "3"]   # comment\n  c: []\n  d:\n'
             '    - {name: "M", n: -1, w: MON}\nitems:\n  - {id: r1, off: {months: 3}, roll: true, ext: none,\n'
             '     basis: "35 USC 21(b)"}\n  - {id: r2, trig: [a, b], off: [{months: 4}, {days: 16}]}\n')
        v = deadlines.parse_mini_yaml(y)
        self.assertEqual(v["top"]["a"], "x # not a comment")
        self.assertEqual(v["top"]["b"], [1, "two", "3"])
        self.assertEqual(v["top"]["c"], [])
        self.assertEqual(v["top"]["d"], [{"name": "M", "n": -1, "w": "MON"}])
        self.assertEqual(v["items"][0], {"id": "r1", "off": {"months": 3}, "roll": True, "ext": "none",
                                         "basis": "35 USC 21(b)"})
        self.assertEqual(v["items"][1]["off"], [{"months": 4}, {"days": 16}])

    def test_reference_rules_load(self):
        r = deadlines.load_rules()
        self.assertEqual(r["deadlines"]["nonfinal_oa_reply"]["offset"], {"months": 3})
        self.assertEqual(r["deadlines"]["nonfinal_oa_reply"]["max_from_trigger_months"], 6)
        self.assertEqual(r["deadlines"]["restriction_reply"]["offset"], {"months": 2})
        self.assertEqual(r["deadlines"]["maintenance_1"]["due"], {"years": 3, "months": 6})
        self.assertEqual(r["deadlines"]["issue_fee"]["ext"], "none")
        self.assertEqual(r["date_rules"]["ad_hoc_closures"], [])


class TestOfficeActionDeadlines(unittest.TestCase):
    def test_saturday_rolls_to_monday(self):
        # Mailed Fri 2026-05-01; 3 months = Sat 2026-08-01 -> Mon 2026-08-03.
        self.assertEqual(D(2026, 8, 1).weekday(), 5)
        d = oa("2026-05-01", "nonfinal")
        self.assertEqual(d["due"]["unrolled"], "2026-08-01")
        self.assertEqual(d["due"]["date"], "2026-08-03")
        self.assertTrue(d["due"]["rolled"])
        self.assertIn("Saturday", " ".join(d["due"]["roll_reason"]))
        # Extensions run from the unrolled date: +1 month = Sep 1 (Tue), not Sep 3.
        self.assertEqual(d["extensions"][0]["unrolled"], "2026-09-01")
        self.assertEqual(d["extensions"][0]["date"], "2026-09-01")
        self.assertEqual(len(d["extensions"]), 3)           # 3 + 3 = 6-month cap
        self.assertEqual(d["cap"]["unrolled"], "2026-11-01")  # Sunday
        self.assertEqual(d["cap"]["date"], "2026-11-02")
        f = d["extensions"][1]["fee"]
        self.assertEqual(f["amounts"]["small"], fees.amount(fees.load_fee_table(), "extension_2_months", "small"))

    def test_federal_holiday_rolls(self):
        # Mailed 2026-08-26; 3 months = Thanksgiving, Thu 2026-11-26 -> Fri 2026-11-27.
        d = oa("2026-08-26", "nonfinal")
        self.assertEqual(d["due"]["unrolled"], "2026-11-26")
        self.assertEqual(d["due"]["date"], "2026-11-27")
        self.assertIn("Thanksgiving", " ".join(d["due"]["roll_reason"]))

    def test_mpep_extension_example(self):
        # MPEP 710.01(a): Jan 31 action, due Apr 30; a 1-month extension ends May 31.
        d = oa("2025-01-31", "nonfinal")
        self.assertEqual(d["due"]["unrolled"], "2025-04-30")
        self.assertEqual(d["extensions"][0]["unrolled"], "2025-05-31")
        self.assertEqual(d["extensions"][0]["date"], "2025-06-02")  # May 31, 2025 is a Saturday
        # Nov 30 + 3 months = Feb 28 (MPEP example)
        self.assertEqual(oa("2026-11-30", "nonfinal")["due"]["unrolled"], "2027-02-28")

    def test_restriction_final_and_allowance(self):
        r = oa("2026-03-10", "restriction")
        self.assertEqual(r["period_months"], 2)
        self.assertEqual(len(r["extensions"]), 4)
        f = oa("2026-03-10", "final")
        self.assertEqual(f["advisory_date"]["unrolled"], "2026-05-10")
        self.assertEqual(f["advisory_date"]["date"], "2026-05-11")
        n = oa("2026-09-10", "notice_of_allowance")
        self.assertEqual(n["extensions"], [])
        self.assertEqual(n["due"]["date"], "2026-12-10")
        s = oa("2026-03-10", "nonfinal", ssp_months=1)
        self.assertEqual(len(s["extensions"]), 5)

    def test_days_left_uses_today_override(self):
        d = oa("2026-05-01", "nonfinal", today="2026-07-31")
        self.assertEqual(d["due"]["days_left"], 3)


class TestOtherDeadlines(unittest.TestCase):
    def test_provisional_feb29(self):
        # Convention (deadlines.md rule 1; _dates.add_months): same day-of-month, else last day of the month.
        p = deadlines.run({"command": "provisional", "filed": "2024-02-29", "today": "2024-03-01"})["deadline"]
        self.assertEqual(p["due"]["unrolled"], "2025-02-28")
        self.assertEqual(p["due"]["date"], "2025-02-28")  # Friday, no roll
        self.assertEqual(p["restore"]["date"], "2025-04-28")
        self.assertEqual(p["reminders"][0]["date"], "2024-11-29")
        self.assertTrue(any("Feb 29" in n for n in p["notes"]))
        p2 = deadlines.run({"command": "provisional", "filed": "2028-02-29"})["deadline"]
        self.assertEqual(p2["due"]["date"], "2029-02-28")

    def test_maintenance_windows(self):
        m = deadlines.run({"command": "maintenance", "grant_date": "2022-03-08", "today": "2026-01-01"})["deadline"]
        s1, s2, s3 = m["stages"]
        self.assertEqual((s1["window_open"], s1["due"], s1["grace_end_unrolled"], s1["grace_end"]),
                         ("2025-03-08", "2025-09-08", "2026-03-08", "2026-03-09"))  # Mar 8, 2026 is a Sunday
        self.assertTrue(s1["status"].startswith("IN GRACE"))
        self.assertEqual((s2["due_unrolled"], s2["due"]), ("2029-09-08", "2029-09-10"))
        self.assertEqual((s3["window_open"], s3["due"], s3["grace_end"]), ("2033-03-08", "2033-09-08", "2034-03-08"))
        self.assertEqual(s1["surcharge"]["key"], "maintenance_grace_surcharge")

    def test_bar_pct_postgrant(self):
        b = deadlines.run({"command": "bar", "disclosed": "2025-07-04"})["deadline"]
        self.assertEqual(b["due"]["date"], "2026-07-06")  # Jul 4 2026 Sat; Fri Jul 3 observed; roll to Mon Jul 6
        p = deadlines.run({"command": "pct", "priority": "2025-06-14"})["deadline"]
        self.assertEqual(p["due"]["date"], "2027-12-14")
        self.assertEqual(p["others"][0]["date"], "2028-01-14")
        r = deadlines.run({"command": "reissue-broadening", "grant_date": "2025-05-06"})["deadline"]
        self.assertEqual(r["due"]["date"], "2027-05-06")
        g = deadlines.run({"command": "pgr", "grant_date": "2026-04-07"})["deadline"]
        self.assertEqual(g["due"]["date"], "2027-01-07")
        i = deadlines.run({"command": "ipr", "grant_date": "2024-04-02", "complaint_served": "2026-01-16"})["deadline"]
        self.assertEqual(i["earliest"]["date"], "2025-01-03")
        self.assertEqual(i["due"]["unrolled"], "2027-01-16")  # Saturday
        self.assertEqual(i["due"]["date"], "2027-01-19")      # Sun, then MLK Day Mon Jan 18
        dmg = deadlines.run({"command": "damages-window", "filed": "2026-11-18"})["deadline"]
        self.assertEqual(dmg["due"]["date"], "2020-11-18")
        self.assertFalse(dmg["due"]["roll_applies"])

    def test_usage_errors(self):
        with self.assertRaises(UsageError):
            deadlines.run({"command": "oa", "mailed": "2026-01-01", "type": "bogus"})
        with self.assertRaises(UsageError):
            deadlines.run({"command": "provisional"})
        with self.assertRaises(UsageError):
            deadlines.run({"command": "bar", "disclosed": "05/01/2026"})


class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        assets = [
            {"id": "A1", "title": "Band", "type": "utility", "status": "pending", "filing_date": "2024-03-14",
             "entity": "small", "events": [{"type": "office_action", "action": "nonfinal", "mailed": "2026-08-26"}]},
            {"id": "A2", "title": "Dock", "type": "provisional", "status": "pending", "filing_date": "2025-12-01",
             "events": []},
            {"id": "A3", "title": "Old patent", "type": "utility", "status": "granted", "grant_date": "2022-03-08",
             "entity": "small", "events": []},
            {"id": "A4", "title": "Replied", "type": "utility", "status": "pending", "filing_date": "2024-01-01",
             "events": [{"type": "final_rejection", "mailed": "2026-01-05"},
                        {"type": "reply_filed", "date": "2026-02-20"}]},
            {"id": "A5", "title": "Late reply", "type": "utility", "status": "pending", "filing_date": "2024-01-01",
             "events": [{"type": "nonfinal_rejection", "mailed": "2026-07-01"}]},
            {"id": "A6", "title": "No data", "type": "utility", "status": "pending"},
            {"id": "A7", "title": "Allowed", "type": "utility", "status": "pending", "filing_date": "2023-01-01",
             "events": [{"type": "notice_of_allowance", "mailed": "2026-10-01"}]},
            {"id": "A8", "title": "Dead", "type": "utility", "status": "abandoned"},
        ]
        with open(os.path.join(self.d, "portfolio.json"), "w") as fh:
            json.dump({"schema": "patentassist/portfolio@1", "assets": assets}, fh)

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_groups(self):
        res = deadlines.run({"command": "portfolio", "dir": self.d, "today": "2026-11-18"})
        g = res["groups"]
        ids = {k: [e["asset"] for e in v] for k, v in g.items() if k != "missing_data"}
        self.assertIn("A1", ids["due_30"])               # due 2026-11-27 (Thanksgiving roll)
        self.assertEqual(g["due_30"][0]["date"], "2026-11-27")
        self.assertIn("A2", ids["due_30"])               # 12-month date Tue 2026-12-01, 13 days out
        self.assertIn("A3", ids["past_all_windows"])     # 3.5-year fee grace ended 2026-03-09
        self.assertIn("A5", ids["overdue_in_grace"])     # due 2026-10-01, extendable to 2027-01-01
        self.assertIn("A7", ids["due_90"])               # issue fee: Jan 1, 2027 (holiday, Fri) -> Mon Jan 4
        self.assertEqual(g["due_90"][0]["date"], "2027-01-04")
        a5 = g["overdue_in_grace"][0]
        self.assertEqual(a5["date"], "2026-12-01")       # reply with a 2-month extension by this date
        self.assertEqual(a5["absolute_limit"], "2027-01-04")
        self.assertNotIn("A4", sum(ids.values(), []))
        self.assertNotIn("A8", sum(ids.values(), []))
        self.assertIn("A6", [m["asset"] for m in g["missing_data"]])
        self.assertEqual(res["exit_code"], 1)

    def test_bad_schema(self):
        with open(os.path.join(self.d, "portfolio.json"), "w") as fh:
            json.dump({"schema": "other@1", "assets": []}, fh)
        with self.assertRaises(UsageError):
            deadlines.run({"command": "portfolio", "dir": self.d})

    def test_cli_text(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = deadlines.main(["portfolio", "--dir", self.d, "--today", "2026-11-18"])
        self.assertEqual(code, 1)
        self.assertIn("OVERDUE BUT IN GRACE", buf.getvalue())
        self.assertIn("last verified", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
