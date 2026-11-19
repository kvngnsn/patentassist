"""Offline tests for scripts/chart.py and scripts/md_to_docx.py."""

import csv
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FIX = os.path.join(HERE, "fixtures", "draft")
sys.path.insert(0, SCRIPTS)

import chart  # noqa: E402

try:
    import docx  # noqa: F401
    HAVE_DOCX = True
except ImportError:
    HAVE_DOCX = False


def _read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def _jload(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _jdump(o, p):
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(o, fh)


class TestChart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.nodir = os.path.join(self.tmp, "no-such-dir")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_validate_good_and_bad(self):
        r = chart.run({"command": "validate", "chart": os.path.join(FIX, "chart_patentability.json"),
                       "dir": self.nodir})
        self.assertEqual(r["exit_code"], 0, r["findings"])
        r = chart.run({"command": "validate", "chart": os.path.join(FIX, "chart_bad.json"), "dir": self.nodir})
        codes = {f["code"] for f in r["findings"] if f["level"] == "BLOCK"}
        self.assertEqual(codes, {"STATE", "CELL_DUP", "CELL_ELEMENT", "VERIFIED"})
        self.assertEqual(r["exit_code"], 1)

    def test_render_md_csv(self):
        base = os.path.join(self.tmp, "out")
        r = chart.run({"command": "render", "chart": os.path.join(FIX, "chart_patentability.json"), "md": True,
                       "csv": True, "out": base, "dir": self.nodir})
        self.assertEqual(r["exit_code"], 0)
        md = _read(base + ".md")
        self.assertTrue(md.startswith("> **DRAFT"))
        self.assertIn("Partial †", md)
        self.assertIn("[0018]", md)
        self.assertIn("“a helmet having an outer shell”", md)
        self.assertIn("(UNVERIFIED)", md)
        self.assertIn("## Needs evidence", md)
        self.assertIn("accelerometer implied", md)
        self.assertIn("\\|", md)  # pipe in a quote is escaped
        rows = list(csv.reader(io.StringIO(_read(base + ".csv"))))
        self.assertEqual(rows[0], chart.CSV_COLS)
        self.assertIn("verified", rows[0])
        r2 = [r for r in rows if r[2] == "R2" and r[0] == "1a"][0]
        self.assertTrue(r2[7].startswith("'="), r2)   # quote neutralized
        self.assertTrue(r2[8].startswith("'-"), r2)   # analysis neutralized

    def test_render_by_element(self):
        md = chart.render_md(chart.load_chart(os.path.join(FIX, "chart_patentability.json")), by="element")
        self.assertIn("| Element |", md)
        self.assertIn("**Explicit** — [0018]", md)

    def test_safe_csv(self):
        for s in ("=1+1", "+1", "-1", "@SUM(A1)", "\tx", "\rx"):
            self.assertEqual(chart.safe_csv(s)[0], "'")
        self.assertEqual(chart.safe_csv("plain"), "plain")

    def test_needs_evidence(self):
        r = chart.run({"command": "needs-evidence", "chart": os.path.join(FIX, "chart_patentability.json"),
                       "dir": self.nodir})
        ne = r["needs_evidence"]
        self.assertTrue(any(n.startswith("1b vs R1") and "construction" in n for n in ne))
        self.assertTrue(any(n.startswith("1b vs R2") and "unknown" in n for n in ne))
        self.assertTrue(any("R2: reference not verified" in n for n in ne))
        self.assertEqual(r["summary"]["unverified_cells"], 4)

    def test_from_prior_art(self):
        d = os.path.join(self.tmp, "patent")
        shutil.copytree(os.path.join(FIX, "matter"), d)
        out = os.path.join(d, "charts", "patentability.json")
        r = chart.run({"command": "from-prior-art", "dir": d, "no_audit": True})
        self.assertEqual(r["exit_code"], 0)
        c = _jload(out)
        self.assertEqual(c["schema"], "patentassist/chart@1")
        self.assertEqual([x["id"] for x in c["refs"]], ["R1", "R2"])  # R3 has no element_map
        self.assertEqual(len(c["cells"]), 6)
        unmapped = [x for x in c["cells"] if x["ref"] == "R1" and x["element"] == "E3"][0]
        self.assertEqual(unmapped["state"], "unknown")  # never collapsed into absent
        self.assertTrue(all(x["verified"] is False for x in c["cells"]))
        self.assertEqual(chart.validate(c), [f for f in chart.validate(c) if f["level"] != "BLOCK"])
        # a person's tick on an unchanged cell survives a rebuild
        c["cells"][0]["verified"] = True
        _jdump(c, out)
        chart.run({"command": "from-prior-art", "dir": d, "no_audit": True})
        self.assertTrue(_jload(out)["cells"][0]["verified"])
        r = chart.run({"command": "from-prior-art", "dir": d, "categories": "X", "no_audit": True,
                       "out": os.path.join(self.tmp, "x.json")})
        self.assertEqual(r["summary"]["refs"], 1)

    def test_schema_refused(self):
        p = os.path.join(self.tmp, "c.json")
        _jdump({"schema": "patentassist/chart@2", "kind": "patentability"}, p)
        with self.assertRaises(chart.UsageError):
            chart.run({"command": "validate", "chart": p, "dir": self.nodir})

    @unittest.skipUnless(HAVE_DOCX, "python-docx not installed")
    def test_render_docx(self):
        base = os.path.join(self.tmp, "out")
        r = chart.run({"command": "render", "chart": os.path.join(FIX, "chart_patentability.json"), "docx": True,
                       "out": base, "dir": self.nodir})
        self.assertEqual(r["written"], [base + ".docx"])
        import docx as _d
        doc = _d.Document(base + ".docx")
        self.assertEqual(len(doc.tables), 2)
        self.assertIn("DRAFT", doc.sections[0].header.paragraphs[0].text)


class TestChartFriction(unittest.TestCase):
    """F20 relative --out under --dir, F21 needs-evidence vs 103 gaps, F22 compact by-element,
    F23 machine-translation tags."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.chart = _jload(os.path.join(FIX, "chart_patentability.json"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_needs_evidence_excludes_partial(self):
        c = self.chart
        c["cells"].append({"element": "1c", "ref": "R2", "state": "inherent", "quote": "q", "pinpoint": "[0003]",
                           "verified": False})
        c["cells"][1]["construction_dependent"] = False  # 1b vs R1: partial only
        c["needs_evidence"].append("1b vs R1: partial (stored by an older build)")
        ne, _ = chart.needs_evidence(c)
        self.assertFalse(any(n.startswith("1b vs R1") for n in ne), ne)
        self.assertTrue(any(n.startswith("1c vs R2") and "inherent" in n for n in ne), ne)
        self.assertTrue(any(n.startswith("1b vs R2") and "unknown" in n for n in ne))
        gaps = chart.gaps_103(c)
        self.assertEqual(len(gaps), 1)
        self.assertTrue(gaps[0].startswith("1b vs R1: partial"), gaps)
        p = os.path.join(self.tmp, "c.json")
        _jdump(c, p)
        r = chart.run({"command": "needs-evidence", "chart": p, "dir": self.tmp})
        self.assertEqual(r["summary"]["gaps_103"], 1)
        md = chart.render_md(c)
        self.assertIn("## 103 gaps (partial matches)", md)
        self.assertLess(md.index("## Needs evidence"), md.index("## 103 gaps"))

    def test_by_element_compact_with_footnotes(self):
        md = chart.render_md(self.chart, by="element")
        table = [ln for ln in md.splitlines() if ln.startswith("| **1a**")][0]
        self.assertIn("**Explicit** \u2014 [0018]", table)
        self.assertNotIn("\u201c", table)                     # no quotes inside the table
        self.assertIn("### Quotes and notes", md)
        self.assertIn("[1] R1 \u00d7 1a ([0018]): \u201ca helmet having an outer shell\u201d", md)
        n_notes = len([ln for ln in md.splitlines() if re.match(r"^\[\d+\] ", ln)])
        self.assertEqual(n_notes, sum(1 for c in self.chart["cells"]
                                      if c.get("quote") or c.get("analysis") or not c.get("verified")))

    def test_machine_translation_tag_from_cache_and_flag(self):
        d = os.path.join(self.tmp, "patent")
        os.makedirs(os.path.join(d, "cache"))
        rec = {"schema": "patentassist/patent@1", "number": "US9457709B2", "notes": [
            "Text is Google machine translation from German; quote it as machine-translated."]}
        _jdump(rec, os.path.join(d, "cache", "US9457709B2.json"))
        p = os.path.join(d, "charts", "c.json")
        os.makedirs(os.path.dirname(p))
        _jdump(self.chart, p)
        r = chart.run({"command": "render", "chart": "charts/c.json", "dir": d, "csv": True, "md": True,
                       "no_audit": True})
        self.assertEqual(r["machine_translated_refs"], ["R1"])
        md = _read(os.path.join(d, "charts", "c.md"))
        r1_rows = [ln for ln in md.splitlines() if "[0018]" in ln and ln.startswith("| **1a**")]
        self.assertIn(chart.MT_TAG, r1_rows[0])
        self.assertEqual(md.count(chart.MT_TAG), 3)          # R1 has three cells; R2 is not translated
        rows = list(csv.reader(io.StringIO(_read(os.path.join(d, "charts", "c.csv")))))
        self.assertEqual({r[2]: r[-1] for r in rows[1:]}, {"R1": "true", "R2": "false"})
        self.chart["refs"][1]["machine_translation"] = True
        self.assertEqual(chart.machine_translated_refs(self.chart, None), {"R2"})

    def test_relative_out_resolves_under_dir(self):
        d = os.path.join(self.tmp, "patent")
        shutil.copytree(os.path.join(FIX, "matter"), d)
        r = chart.run({"command": "from-prior-art", "dir": d, "out": "charts/pat.json", "no_audit": True})
        self.assertEqual(r["written"], [os.path.join(d, "charts", "pat.json")])
        self.assertTrue(os.path.exists(os.path.join(d, "charts", "pat.json")))
        r = chart.run({"command": "render", "chart": "charts/pat.json", "dir": d, "out": "reports/chart",
                       "no_audit": True})
        self.assertEqual(r["written"], [os.path.join(d, "reports", "chart.md")])
        self.assertEqual(chart.under_dir("patent/charts/x.json", "patent"), "patent/charts/x.json")
        self.assertEqual(chart.under_dir("charts/x.json", "patent"), os.path.join("patent", "charts", "x.json"))
        self.assertEqual(chart.under_dir("/abs/x.json", "patent"), "/abs/x.json")


@unittest.skipUnless(HAVE_DOCX, "python-docx not installed")
class TestMdToDocx(unittest.TestCase):
    def test_convert(self):
        import md_to_docx
        tmp = tempfile.mkdtemp()
        try:
            src = os.path.join(tmp, "r.md")
            with open(src, "w") as fh:
                fh.write("---\ntitle: x\n---\n# Report\n\n## Findings\n\n- one\n- **two**\n\n1. first\n\n"
                         "| a | b |\n|---|---|\n| 1 | 2 |\n\n> note\n\nBody text.\n")
            r = md_to_docx.run({"input": src, "draft": True, "no_audit": True})
            self.assertTrue(r["ok"], r)
            import docx as _d
            doc = _d.Document(r["output"])
            self.assertEqual(len(doc.tables), 1)
            self.assertEqual(doc.styles["Normal"].font.name, "Times New Roman")
            self.assertIn("DRAFT", doc.sections[0].header.paragraphs[0].text)
            texts = [p.text for p in doc.paragraphs]
            self.assertIn("Report", texts)
            self.assertTrue(any(t.startswith("•\tone") for t in texts))
            self.assertFalse(any("title: x" in t for t in texts))
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
