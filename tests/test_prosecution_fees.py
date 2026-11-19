"""Offline tests for scripts/fees.py. Expected amounts are recomputed from the json block in
references/fees.md (the only source of dollar amounts), so the tests follow fee updates."""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import fees  # noqa: E402
from state import UsageError  # noqa: E402


def table_from_md():
    with open(os.path.join(ROOT, "references", "fees.md"), encoding="utf-8") as fh:
        text = fh.read()
    start = text.index("## Machine-readable fees")
    m = re.search(r"```json\n(.*?)```", text[start:], re.S)
    return json.loads(m.group(1))


T = table_from_md()
F = T["fees"]


def run(**kw):
    kw.setdefault("command", "estimate")
    return fees.run(kw)


class TestEstimate(unittest.TestCase):
    def test_small_nonprov_4_indep_25_total_120_pages(self):
        """Small entity, e-filed DOCX, 4 independent / 25 total claims, 120 rendered pages.

        Hand computation from fees.md (Nov 2026 table): basic e-filed 70 + search 308 + exam 352
        + 1 excess independent x 240 + 5 excess total x 80 = 1,370. 120 rendered sheets x 0.75 =
        90 counted sheets, so no size fee when e-filed."""
        res = run(type="nonprovisional", entity="small", independent=4, total=25, pages=120)
        est = res["estimate"]
        expected = (F["utility_basic_filing_efiled"]["small"] + F["utility_search"]["small"]
                    + F["utility_examination"]["small"] + 1 * F["excess_independent_claim"]["small"]
                    + 5 * F["excess_total_claim"]["small"])
        self.assertEqual(est["total"], expected)
        self.assertEqual(expected, 1370)  # snapshot of the 2026-11-18 table; update with fees.md
        self.assertEqual(est["counted_sheets"], 90)
        keys = [i["key"] for i in est["items"]]
        self.assertNotIn("utility_size_fee", keys)
        by = {i["key"]: i for i in est["items"]}
        self.assertEqual(by["excess_independent_claim"]["count"], 1)
        self.assertEqual(by["excess_total_claim"]["count"], 5)
        self.assertEqual(by["utility_basic_filing_efiled"]["code"], 4011)
        self.assertEqual(res["last_verified"], F["_meta"]["last_verified"])
        self.assertIn("Verify on uspto.gov fee schedule before paying; table last verified %s"
                      % F["_meta"]["last_verified"], "\n".join(res["text"]))

    def test_size_fee_when_120_sheets_count(self):
        """Same claims, but 120 sheets counted (paper rule or already adjusted): one 50-sheet unit."""
        res = run(type="nonprovisional", entity="small", independent=4, total=25, counted_sheets=120)
        base = 1370 if F["utility_size_fee"]["small"] == 180 else None
        self.assertEqual(res["estimate"]["total"],
                         F["utility_basic_filing_efiled"]["small"] + F["utility_search"]["small"]
                         + F["utility_examination"]["small"] + F["excess_independent_claim"]["small"]
                         + 5 * F["excess_total_claim"]["small"] + F["utility_size_fee"]["small"])
        if base:
            self.assertEqual(res["estimate"]["total"], 1550)
        res = run(type="nonprovisional", entity="large", independent=3, total=20, counted_sheets=151)
        by = {i["key"]: i for i in res["estimate"]["items"]}
        self.assertEqual(by["utility_size_fee"]["count"], 2)  # 51 over 100 -> 2 units of 50 (fraction counts)

    def test_paper_filing_uses_full_count_and_surcharges(self):
        res = run(type="nonprovisional", entity="micro", independent=1, total=5, pages=101, paper=True)
        by = {i["key"]: i for i in res["estimate"]["items"]}
        self.assertEqual(by["utility_basic_filing"]["unit"], F["utility_basic_filing"]["micro"])
        self.assertEqual(by["non_electronic_filing"]["unit"], F["non_electronic_filing"]["micro"])
        self.assertIn("non_docx_surcharge", by)
        self.assertEqual(by["utility_size_fee"]["count"], 1)

    def test_multiple_dependent_and_flags(self):
        res = run(type="nonprovisional", entity="large", independent=2, total=22, multiple_dependent=1, docx="no",
                  late_declaration=True, extension_months=2, ids=120)
        by = {i["key"]: i for i in res["estimate"]["items"]}
        self.assertEqual(by["multiple_dependent_claim"]["subtotal"], F["multiple_dependent_claim"]["large"])
        self.assertEqual(by["non_docx_surcharge"]["subtotal"], F["non_docx_surcharge"]["large"])
        self.assertEqual(by["late_filing_surcharge"]["subtotal"], F["late_filing_surcharge"]["large"])
        self.assertEqual(by["extension_2_months"]["subtotal"], F["extension_2_months"]["large"])
        self.assertEqual(by["ids_size_over_100"]["subtotal"], F["ids_size_over_100"]["large"])
        self.assertEqual(by["excess_total_claim"]["count"], 2)

    def test_continuing_fee_by_years(self):
        res = run(type="nonprovisional", entity="small", continuing=True, earliest_benefit="2018-01-10",
                  filing_date="2026-11-18")
        keys = [i["key"] for i in res["estimate"]["items"]]
        self.assertIn("continuing_6_to_9y", keys)
        res = run(type="nonprovisional", entity="small", continuing=True, earliest_benefit="2016-01-10",
                  filing_date="2026-11-18")
        self.assertIn("continuing_over_9y", [i["key"] for i in res["estimate"]["items"]])
        res = run(type="nonprovisional", entity="small", continuing=True, earliest_benefit="2021-01-10",
                  filing_date="2026-11-18")
        self.assertFalse([i for i in res["estimate"]["items"] if i["key"].startswith("continuing")])

    def test_provisional(self):
        res = run(type="provisional", entity="micro", pages=140)  # 105 counted -> 1 unit
        by = {i["key"]: i for i in res["estimate"]["items"]}
        self.assertEqual(by["provisional_filing"]["unit"], F["provisional_filing"]["micro"])
        self.assertEqual(by["provisional_size_fee"]["count"], 1)
        self.assertEqual(res["estimate"]["total"], F["provisional_filing"]["micro"] + F["provisional_size_fee"]["micro"])

    def test_claims_file_counts(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "claims.md")
            with open(p, "w") as fh:
                fh.write("# Claims\n\n1. A widget comprising a lever.\n\n2. The widget of claim 1, wherein the lever is "
                         "steel.\n\n3. The widget of claim 1 or 2, wherein the lever is long.\n\n4. The widget of claim "
                         "3, wherein the lever is red.\n\n5. A method comprising pulling a lever.\n")
            res = run(type="nonprovisional", entity="large", claims=p)
            by = {i["key"]: i for i in res["estimate"]["items"]}
            # 1 + 1 + 2 (MD refers to 2) + 2 (depends from the MD claim) + 1 = 7 total; 2 independent
            self.assertIn("multiple_dependent_claim", by)
            self.assertNotIn("excess_total_claim", by)
            counts = fees.count_claims_file(p)
            self.assertEqual(counts["independent"], 2)
            self.assertEqual(counts["total_for_fees"], 7)
            with open(p) as fh:
                mini = fees._minimal_parse(fh.read())
            self.assertEqual((mini["independent"], mini["total_for_fees"]), (2, 7))
        finally:
            shutil.rmtree(d)

    def test_national_stage_refused(self):
        with self.assertRaises(UsageError):
            run(type="national_stage", entity="small")


class TestOtherCommands(unittest.TestCase):
    def test_issue_rce_appeal_extension(self):
        r = fees.run({"command": "issue", "entity": "micro"})
        self.assertEqual(r["estimate"]["total"], F["utility_issue"]["micro"])
        r = fees.run({"command": "rce", "entity": "small", "subsequent": True})
        self.assertEqual(r["estimate"]["total"], F["rce_subsequent"]["small"])
        r = fees.run({"command": "appeal", "entity": "large"})
        self.assertEqual(r["estimate"]["total"], F["notice_of_appeal"]["large"] + F["appeal_forwarding"]["large"])
        r = fees.run({"command": "extension", "entity": "large", "months": 3})
        self.assertEqual(r["estimate"]["total"], F["extension_3_months"]["large"])
        with self.assertRaises(UsageError):
            fees.run({"command": "extension", "entity": "large", "months": 6})

    def test_maintenance_schedule(self):
        r = fees.run({"command": "maintenance", "grant_date": "2022-03-08", "entity": "small", "today": "2026-01-01"})
        st = r["maintenance"]
        self.assertEqual([s["fee"]["small"] for s in st],
                         [F["maintenance_3_5y"]["small"], F["maintenance_7_5y"]["small"], F["maintenance_11_5y"]["small"]])
        self.assertEqual(st[0]["entity_fee_with_surcharge"],
                         F["maintenance_3_5y"]["small"] + F["maintenance_grace_surcharge"]["small"])
        self.assertTrue(st[0]["status"].startswith("IN GRACE"))

    def test_cli_default_estimate(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = fees.main(["--type", "provisional", "--entity", "small", "--json"])
        self.assertEqual(code, 0)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["estimate"]["total"], F["provisional_filing"]["small"])
        self.assertIn("last verified", out["verify"])


if __name__ == "__main__":
    unittest.main()


class TestFeeSheetOut(unittest.TestCase):
    """F36: phase 3 expects draft/out/fees.md, but fees.py only printed to stdout."""

    def test_out_writes_md_and_json_with_counts(self):
        import shutil
        import tempfile
        import check_package
        tmp = tempfile.mkdtemp()
        try:
            claims = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "draft", "clean_claims.md")
            res = fees.run({"command": "estimate", "type": "nonprovisional", "entity": "small", "claims": claims,
                            "out": os.path.join(tmp, "out"), "dir": tmp, "no_audit": True})
            self.assertEqual(sorted(os.path.basename(p) for p in res["written"]), ["fees.json", "fees.md"])
            with open(os.path.join(tmp, "out", "fees.json")) as fh:
                obj = json.load(fh)
            self.assertEqual(obj["claim_counts"]["independent"], 3)
            self.assertTrue(obj["claim_counts"]["claim_fees_apply"])
            self.assertEqual(obj["total"], res["estimate"]["total"])
            gi, gt, how = check_package._counts_from_sheet(os.path.join(tmp, "out", "fees.json"))
            self.assertEqual((gi, gt), (3, obj["claim_counts"]["total_for_fees"]))
            gi2, gt2, _ = check_package._counts_from_sheet(os.path.join(tmp, "out", "fees.md"))
            self.assertEqual((gi2, gt2), (gi, gt))
        finally:
            shutil.rmtree(tmp)
