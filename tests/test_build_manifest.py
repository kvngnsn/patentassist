"""Offline tests for scripts/manifest.py (filing package manifest with Patent Center descriptions)."""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FILING = os.path.join(HERE, "fixtures", "build", "filing.json")
sys.path.insert(0, SCRIPTS)

import manifest  # noqa: E402


def touch(p, data=b"x"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(data)


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.d = os.path.join(self.tmp, "patent")
        self.out = os.path.join(self.d, "draft", "out")
        os.makedirs(self.out)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def filing(self, **over):
        with open(FILING) as fh:
            f = json.load(fh)
        f.update(over)
        with open(os.path.join(self.d, "draft", "filing.json"), "w") as fh:
            json.dump(f, fh)

    def test_descriptions_block_covers_both_filing_types(self):
        desc = manifest.load_descriptions()
        self.assertTrue(desc["last_verified"])
        for key, by_type in desc["documents"].items():
            for t in ("provisional", "nonprovisional"):
                self.assertEqual(len(by_type[t]), 4, key)
                self.assertIn(by_type[t][2], ("required", "conditional", "optional", "not_allowed", "n/a"), key)
        self.assertEqual(desc["documents"]["cover_sheet"]["provisional"][0], "Provisional Cover Sheet (SB16)")
        self.assertEqual(desc["documents"]["drawings"]["nonprovisional"][0],
                         "Drawings-only black and white line drawings")

    def test_provisional_package(self):
        self.filing()   # provisional, micro, gross income
        touch(os.path.join(self.out, "spec.docx"), b"docx")
        touch(os.path.join(self.out, "drawings.pdf"), b"%PDF")
        touch(os.path.join(self.out, "sb16-worksheet.md"), b"# worksheet")
        touch(os.path.join(self.out, "ids.json"), b"{}")
        touch(os.path.join(self.d, "draft", "figures.json"), b"{}")
        res = manifest.run({"dir": self.d, "no_audit": False})
        files = {f["file"]: f for f in res["manifest"]["files"]}
        self.assertEqual(files["spec.docx"]["description"], "Specification")
        self.assertEqual(files["drawings.pdf"]["doc_code"], "DRW")
        self.assertFalse(files["sb16-worksheet.md"]["upload"])
        self.assertEqual(len(files["spec.docx"]["sha256"]), 64)
        self.assertEqual(files["spec.docx"]["size"], 4)
        where = [f["where"] for f in res["findings"]]
        self.assertIn("cover sheet", where)
        self.assertIn("micro entity certification", where)
        self.assertEqual(res["exit_code"], 0)
        with open(os.path.join(self.out, "manifest.md")) as fh:
            md = fh.read()
        self.assertIn("| spec.docx | Specification | SPEC |", md)
        with open(os.path.join(self.d, "audit.jsonl")) as fh:
            recs = [json.loads(x) for x in fh]
        self.assertEqual([r["path"] for r in recs if r["kind"] == "export"],
                         ["draft/out/manifest.md", "draft/out/manifest.json"])
        # running again does not list its own output
        res2 = manifest.run({"dir": self.d, "no_audit": True})
        self.assertNotIn("manifest.md", [f["file"] for f in res2["manifest"]["files"]])

    def test_ids_in_provisional_blocks(self):
        self.filing(entity_status="small")
        touch(os.path.join(self.out, "spec.docx"))
        touch(os.path.join(self.out, "sb16-filled.pdf"))
        touch(os.path.join(self.out, "sb08-filled.pdf"))
        res = manifest.run({"dir": self.d, "no_audit": True})
        self.assertIn("NOT_ALLOWED", [f["code"] for f in res["findings"] if f["level"] == "BLOCK"])
        files = {f["file"]: f for f in res["manifest"]["files"]}
        self.assertEqual(files["sb16-filled.pdf"]["description"], "Provisional Cover Sheet (SB16)")
        self.assertFalse(files["sb08-filled.pdf"]["upload"])
        self.assertEqual(res["exit_code"], 1)

    def test_nonprovisional_split_docx_needs_claims_and_abstract(self):
        self.filing(filing_type="nonprovisional", entity_status="small")
        touch(os.path.join(self.out, "specification.docx"))
        touch(os.path.join(self.out, "claims.docx"))
        touch(os.path.join(self.out, "aia01-inventor1-filled.pdf"))
        res = manifest.run({"dir": self.d, "no_audit": True})
        msgs = [f["message"] for f in res["findings"] if f["level"] == "BLOCK"]
        self.assertTrue(any("abstract" in m for m in msgs), res["findings"])
        files = {f["file"]: f for f in res["manifest"]["files"]}
        self.assertEqual(files["aia01-inventor1-filled.pdf"]["description"], "Oath or Declaration filed")
        self.assertEqual(files["claims.docx"]["requirement"], "required")

    def test_combined_docx_nonprovisional(self):
        self.filing(filing_type="nonprovisional", entity_status="small")
        touch(os.path.join(self.out, "spec.docx"))
        res = manifest.run({"dir": self.d, "no_audit": True})
        f = res["manifest"]["files"][0]
        self.assertEqual(f["description"], "Application body structured text document")
        self.assertFalse([x for x in res["findings"] if x["level"] == "BLOCK"])

    def test_no_out_folder_is_usage_error(self):
        shutil.rmtree(self.out)
        with self.assertRaises(manifest.UsageError):
            manifest.run({"dir": self.d, "no_audit": True})


if __name__ == "__main__":
    unittest.main()
