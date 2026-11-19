"""Date-mechanics drills D-1 ... D-26 (references/case-law/edge-case-drills.md, Part 2) encoded
against the scripts that compute them: state.compute_bar (1-year grace + 21(b) roll),
deadlines.py calculators and rules (maintenance, PCT, reissue, PGR/IPR, 286, priority windows),
verify_refs.compute_basis (102(a)(1) / 102(a)(2) dating), and _dates (calendar months, roll).

Each test asserts the drill's stated answer. Parts of a drill that need legal judgment (AIA vs
pre-AIA status, same-subject-matter shields, diligence, filing-date requirements, forum rules) are
not computable here and are marked "judgment" in comments; only the dates are checked.
"""

import datetime as dt
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import deadlines as D  # noqa: E402
from _dates import add_months, holiday_name, parse_date, roll_forward  # noqa: E402
from state import compute_bar  # noqa: E402
from verify_refs import compute_basis  # noqa: E402

TODAY = "2026-11-18"


def P(s):
    return parse_date(s)


def term(filed):
    """35 USC 154(a)(2): 20 years from the filing date of the earliest 120/121/365(c) application."""
    return add_months(P(filed), 240)


def rolled(base, rid, which="offset"):
    """Apply a deadlines.md rule's offset to `base` and roll it (35 USC 21(b))."""
    r = D.rule(rid)
    off = r[which]
    if isinstance(off, list):
        off = off[1]
    return D.roll(D.offset_date(P(base), off))[0]


def bar(**dates):
    return compute_bar(dates, TODAY)


class TestTermAndMaintenance(unittest.TestCase):
    def test_d1_continuation_term_and_missed_maintenance_fee(self):
        self.assertEqual(term("2016-04-11"), P("2036-04-11"))  # from the earliest 120 application
        self.assertNotEqual(term("2019-02-04"), P("2036-04-11"))  # trap: the continuation's own date (2039)
        m = D.maintenance_window("2020-09-15", "maintenance_1")
        self.assertEqual((m["window_open"], m["due"]), ("2023-09-15", "2024-03-15"))
        self.assertEqual(m["grace_end_unrolled"], "2024-09-15")  # expires at the end of the grace period
        self.assertEqual(P("2024-09-15").weekday(), 6)  # a Sunday ...
        self.assertEqual(m["grace_end"], "2024-09-16")  # ... so Monday payment is timely (1.362(f); 21(b))

    def test_d2_paris_priority_pta_terminal_disclaimer(self):
        self.assertEqual(rolled("2021-06-08", "paris_priority_us_filing"), P("2022-06-08"))
        self.assertLessEqual(P("2022-06-02"), P("2022-06-08"))  # priority timely
        base = term("2022-06-02")  # 154(a)(3): not from the Japanese date
        self.assertEqual(base, P("2042-06-02"))
        self.assertNotEqual(base, term("2021-06-08"))  # trap: 2041-06-08
        with_pta = base + dt.timedelta(days=140)
        self.assertEqual(with_pta, P("2042-10-20"))
        self.assertEqual(min(with_pta, P("2041-12-01")), P("2041-12-01"))  # 154(b)(2)(B): no PTA past disclaimer

    def test_d3_provisional_counts_for_priority_not_term(self):
        due = D.provisional_deadlines(P("2023-01-17"))["due"]["date"]
        self.assertEqual(due, "2024-01-17")
        self.assertLessEqual(P("2024-01-16"), P(due))  # nonprovisional within 12 months
        self.assertEqual(term("2024-01-16"), P("2044-01-16"))  # 154(a)(3): provisional not counted
        # claim 7 (silver variant first in the nonprovisional): EFD 2024-01-16; talk 2023-03-01 is inside
        # the grace period but kills absolute-novelty foreign rights
        b = bar(earliest_public_disclosure="2023-03-01", nonprovisional_filed="2024-01-16")
        self.assertEqual((b["us_status"], b["foreign_status"]), ("clear", "likely_lost"))
        # claim 1 (supported by the provisional): filed before the talk; the note warns that a later-disclosed
        # variant the filing does not describe has its own clock (judgment: which claims are supported)
        b = bar(earliest_public_disclosure="2023-03-01", provisional_filed="2023-01-17")
        self.assertEqual((b["us_status"], b["foreign_status"]), ("clear", "intact"))
        self.assertTrue(any("does not describe" in n for n in b["notes"]))

    def test_d4_pct_national_stage_and_term(self):
        due = D.pct_deadlines(P("2021-05-12"))["due"]
        self.assertEqual(due["unrolled"], "2023-11-12")  # Sunday
        self.assertTrue(holiday_name(P("2023-11-10")).startswith("Veterans Day"))  # observed Fri (Nov 11 is Sat)
        self.assertEqual(due["date"], "2023-11-13")
        self.assertEqual(term("2022-05-10"), P("2042-05-10"))  # from the PCT filing date (363; 154(a)(2))

    def test_d5_reissue_broadening_window_and_term(self):
        due = D.reissue_deadline(P("2018-02-06"))["due"]["date"]
        self.assertEqual(due, "2020-02-06")
        self.assertLessEqual(P("2019-11-01"), P(due))  # broadening allowed (251(d))
        self.assertEqual(term("2015-08-20"), P("2035-08-20"))  # unexpired part of the original term (251(a))

    def test_d6_broadening_reissue_of_continuation(self):
        self.assertEqual(D.reissue_deadline(P("2024-12-17"))["due"]["date"], "2026-12-17")
        self.assertNotEqual(add_months(P("2024-04-11"), 24), P("2026-12-17"))  # trap: from publication

    def test_d7_suing_after_expiry(self):
        expiry = term("2014-09-09")
        self.assertEqual(expiry, P("2034-09-09"))
        earliest = P(D.damages_window(P("2040-09-05"))["due"]["date"])  # complaint in early September 2040
        self.assertEqual(earliest, P("2034-09-05"))
        self.assertLess(earliest, expiry)  # still reaches the last days of the term
        # judgment: claim 15 intervening rights and damages from the 2022-05-03 reissue (252)

    def test_d8_damages_window_and_provisional_rights(self):
        self.assertEqual(D.damages_window(P("2025-03-03"))["due"]["date"], "2019-03-03")  # 286
        last_for_154d = add_months(P("2018-10-09"), 72)  # 154(d)(3): suit within 6 years of grant
        self.assertEqual(last_for_154d, P("2024-10-09"))
        self.assertGreater(P("2025-03-03"), last_for_154d)  # suit in 2025 is too late for provisional rights
        # judgment: marking (287(a)) moves the start to actual notice, 2021-01-15, for apparatus claims


class TestPtabWindows(unittest.TestCase):
    def test_d9_pgr_deadline_and_first_ipr_day(self):
        self.assertEqual(D.pgr_deadline(P("2025-07-15"))["due"]["date"], "2026-04-15")  # 321(c) "not later than"
        self.assertEqual(D.ipr_deadlines(P("2025-07-15"))["earliest"]["date"], "2026-04-16")  # 311(c) "after"

    # D-10: judgment (AIA status decides whether 42.102(a)(2) removes the 9-month wait; no PGR pre-AIA).

    def test_d11_315b_clock_runs_from_service(self):
        item = D.ipr_deadlines(P("2020-01-01"), served=P("2025-02-24"))
        self.assertEqual(item["due"]["date"], "2026-02-24")  # from service, not filing (2025-02-10)
        self.assertNotEqual(add_months(P("2025-02-10"), 12), P(item["due"]["date"]))
        # judgment: 315(a)(1) DJ bar vs 315(a)(3) counterclaim

    def test_d12_full_ptab_calendar(self):
        self.assertEqual(D.pgr_deadline(P("2026-01-20"))["due"]["date"], "2026-10-20")
        ipr = D.ipr_deadlines(P("2026-01-20"), served=P("2026-02-02"))
        opens, closes = P(ipr["earliest"]["date"]), P(ipr["due"]["date"])
        self.assertEqual((opens, closes), (P("2026-10-21"), P("2027-02-02")))
        self.assertTrue(100 <= (closes - opens).days <= 110)  # "only about 3.5 months wide"

    def test_d26_pgr_window_already_closed(self):
        pgr = D.pgr_deadline(P("2025-01-14"), today=P("2025-11-01"))["due"]
        self.assertEqual(pgr["date"], "2025-10-14")
        self.assertLess(pgr["days_left"], 0)  # in November 2025 only IPR (or reexam) remains
        # (a) the patentee's own demo 2022-03-01 is more than a year before the 2023-04-03 EFD
        self.assertEqual(bar(earliest_public_use="2022-03-01", nonprovisional_filed="2023-04-03")["us_status"],
                         "likely_barred")
        # (b) the patentee's brochure 2022-10-01 is within the year (2023-10-01 is a Sunday -> 2023-10-02)
        b = bar(earliest_public_disclosure="2022-10-01", nonprovisional_filed="2023-04-03")
        self.assertEqual((b["us_status"], b["us_last_day"]), ("clear", "2023-10-02"))
        # (e) third-party article 2022-02-15 is 102(a)(1); (d) public only from 2023-05-01: not prior art
        self.assertEqual(compute_basis({"type": "npl", "pub_date": "2022-02-15"}, "2023-04-03")[0], "102(a)(1)")
        self.assertEqual(compute_basis({"type": "npl", "pub_date": "2023-05-01"}, "2023-04-03")[0], "not_prior_art")
        # judgment: (a) and (c) are not IPR grounds (311(b)); confidential distribution of (d)


class TestGraceAndPriorArtDating(unittest.TestCase):
    def test_d13_grace_period_rolls(self):
        self.assertEqual(P("2026-02-14").weekday(), 5)  # Saturday
        self.assertEqual(holiday_name(P("2026-02-16")), "Washington's Birthday")
        b = bar(earliest_public_disclosure="2025-02-14", nonprovisional_filed="2026-02-17")
        self.assertEqual((b["us_status"], b["us_last_day"], b["foreign_status"]),
                         ("clear", "2026-02-17", "likely_lost"))
        self.assertEqual(D.bar_deadline(P("2025-02-14"))["due"]["date"], "2026-02-17")
        self.assertEqual(roll_forward(P("2026-02-14")), P("2026-02-17"))

    def test_d14_dates_only(self):
        b = bar(earliest_public_disclosure="2024-05-01", nonprovisional_filed="2025-04-20")
        self.assertEqual(b["us_status"], "clear")  # the inventor's own article is inside the grace period
        self.assertEqual(compute_basis({"type": "npl", "pub_date": "2024-07-15"}, "2025-04-20")[0], "102(a)(1)")
        # judgment: 102(b)(1)(B) shields only the same subject matter (titanium, not carbon fiber)

    def test_d15_foreign_priority_dates_a_102a2_reference(self):
        self.assertEqual(rolled("2022-03-01", "paris_priority_us_filing"), P("2023-03-01"))
        self.assertLessEqual(P("2023-02-27"), P("2023-03-01"))  # the rival's US filing was timely
        ref = {"type": "application", "number": "US20230300001A1", "priority_date": "2022-03-01",
               "filing_date": "2023-02-27", "pub_date": "2023-09-07"}
        self.assertEqual(compute_basis(ref, "2022-11-10")[0], "102(a)(2)")  # effective 2022-03-01 (102(d)(2))
        no_support = dict(ref)
        no_support.pop("priority_date")  # German filing does not describe the subject matter
        self.assertEqual(compute_basis(no_support, "2022-11-10")[0], "not_prior_art")
        # judgment: pre-AIA Hilmer dating, and whether the foreign filing describes the subject matter

    def test_d16_foreign_only_application_never_102a2(self):
        cn = {"type": "application", "number": "CN115100001A", "filing_date": "2021-08-01", "pub_date": "2023-02-01"}
        self.assertEqual(compute_basis(cn, "2022-06-01")[0], "not_prior_art")
        wo = {"type": "application", "number": "WO2022100001A1", "priority_date": "2021-08-01",
              "pub_date": "2023-02-01"}
        self.assertEqual(compute_basis(wo, "2022-06-01")[0], "102(a)(2)")

    def test_d17_missed_paris_deadline_restorable(self):
        r = D.rule("paris_priority_us_filing")
        twelve = D.offset_date(P("2024-03-05"), r["offset"])
        self.assertEqual(twelve, P("2025-03-05"))
        restore_end = add_months(twelve, int(r["restore"]["window_months"]))
        self.assertEqual(restore_end, P("2025-05-05"))  # 119(a); 37 CFR 1.55(c)
        self.assertTrue(twelve < P("2025-04-28") <= restore_end)
        article = {"type": "npl", "pub_date": "2024-11-12"}
        self.assertEqual(compute_basis(article, "2024-03-05")[0], "not_prior_art")  # restored
        self.assertEqual(compute_basis(article, "2025-04-28")[0], "102(a)(1)")  # not restored

    def test_d18_same_text_is_not_a_priority_claim(self):
        r = D.rule("foreign_priority_claim_in_ads")
        four = D.roll(D.offset_date(P("2024-06-24"), r["offset"][0]))[0]
        sixteen = D.roll(D.offset_date(P("2023-07-03"), r["offset"][1]))[0]
        self.assertEqual(four, P("2024-10-24"))
        self.assertEqual(D.offset_date(P("2023-07-03"), r["offset"][1]), P("2024-11-03"))  # a Sunday
        self.assertEqual(sixteen, P("2024-11-04"))
        self.assertEqual(max(four, sixteen), P("2024-11-04"))  # 1.55(d): the later of the two
        article = {"type": "npl", "pub_date": "2024-01-10"}
        self.assertEqual(compute_basis(article, "2024-06-24")[0], "102(a)(1)")  # no priority claim yet
        self.assertEqual(compute_basis(article, "2023-07-03")[0], "not_prior_art")  # claim made in time

    # D-19: judgment (an application that ever contained an AIA claim is AIA for every claim, 3(n)(1)).

    def test_d20_pre_aia_critical_date(self):
        critical = add_months(P("2011-09-14"), -12)
        self.assertEqual(critical, P("2010-09-14"))
        self.assertLess(P("2010-08-01"), critical)  # (b): a 102(b) bar, cannot be antedated
        self.assertGreaterEqual(P("2011-02-01"), critical)  # (a): 102(a) art only, can be antedated
        # judgment: Rule 131 showings and 102(e) dating of (c)

    # D-21: judgment (pre-AIA diligence from just before the rival's conception).

    def test_d22_private_sale_starts_the_clock(self):
        b = bar(earliest_sale_or_offer="2024-01-20", nonprovisional_filed="2024-09-30")
        self.assertEqual((b["us_status"], b["foreign_status"]), ("clear", "at_risk"))
        q = {"type": "application", "number": "US20250300001A1", "filing_date": "2024-03-01",
             "pub_date": "2025-09-04"}
        self.assertEqual(compute_basis(q, "2024-09-30")[0], "102(a)(2)")  # Q's application is art against P
        # judgment: a private sale is not a 102(b)(2)(B) public disclosure (Sanho)

    def test_d23_nobody_gets_a_patent(self):
        b = bar(earliest_public_disclosure="2023-02-10", nonprovisional_filed="2024-03-01")
        self.assertEqual(P("2024-02-10").weekday(), 5)  # Saturday -> Monday 2024-02-12
        self.assertEqual((b["us_status"], b["us_last_day"]), ("likely_barred", "2024-02-12"))
        self.assertEqual(rolled("2023-06-15", "paris_priority_us_filing"), P("2024-06-17"))  # S timely (06-10)
        self.assertEqual(compute_basis({"type": "npl", "pub_date": "2023-02-10"}, "2023-06-15")[0], "102(a)(1)")

    def test_d24_online_first_beats_print_date(self):
        b = bar(earliest_public_disclosure="2024-08-20", nonprovisional_filed="2025-08-25")
        self.assertEqual((b["us_status"], b["us_last_day"]), ("likely_barred", "2025-08-20"))
        self.assertEqual(P("2025-08-20").weekday(), 2)  # a Wednesday: no roll
        # judgment: confidential submission (2024-02-01) is not a disclosure

    # D-25: judgment (111(a)(4) filing-date requirements; nothing to compute).


if __name__ == "__main__":
    unittest.main()
