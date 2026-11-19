"""Offline tests for scripts/fill_forms.py (USPTO form worksheets and AcroForm filling)."""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
FIX = os.path.join(HERE, "fixtures", "build")
sys.path.insert(0, SCRIPTS)

import fill_forms  # noqa: E402

try:
    import pypdf  # noqa: F401
    HAVE_PYPDF = True
except ImportError:
    HAVE_PYPDF = False
try:
    import reportlab  # noqa: F401
    HAVE_RL = True
except ImportError:
    HAVE_RL = False

FILING = os.path.join(FIX, "filing.json")


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def make_acroform(path):
    """A small AcroForm shaped like PTO/SB/16 (same field names), made offline with reportlab."""
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(path, pagesize=(612, 792))
    f = c.acroForm
    y = 700
    for name in ("Given Name first and middle if anyRow1", "Family Name or SurnameRow1",
                 "Residence City and either State or Foreign CountryRow1",
                 "TITLE OF THE INVENTION 500 characters maxRow1", "TYPED OR PRINTED NAME", "DOCKET NUMBER"):
        f.textfield(name=name, tooltip=name, x=72, y=y, width=400, height=18)
        y -= 30
    f.textfield(name="signature", tooltip="Enter your signature", x=72, y=y, width=300, height=18)
    y -= 30
    f.textfield(name="DATE", tooltip="DATE", x=72, y=y, width=120, height=18)
    y -= 30
    for name in ("SE", "ME"):
        f.checkbox(name=name, tooltip=name, x=72, y=y, size=12, buttonStyle="check", checked=False)
        y -= 24
    c.showPage()
    c.save()


def make_xfa(path):
    """A PDF that declares dynamic XFA (NeedsRendering) with no AcroForm widgets, like the current ADS."""
    from pypdf import PdfWriter
    from pypdf.generic import ArrayObject, BooleanObject, DictionaryObject, NameObject, TextStringObject
    w = PdfWriter()
    w.add_blank_page(612, 792)
    w._root_object[NameObject("/AcroForm")] = DictionaryObject({
        NameObject("/Fields"): ArrayObject(),
        NameObject("/XFA"): ArrayObject([TextStringObject("template"), TextStringObject("<template/>")])})
    w._root_object[NameObject("/NeedsRendering")] = BooleanObject(True)
    with open(path, "wb") as fh:
        w.write(fh)


class WorksheetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pa-forms-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sb16_worksheet_nulls_ask_user_and_no_signature(self):
        res = fill_forms.operate("worksheet", "SB16", FILING, self.tmp)
        ws = read(os.path.join(self.tmp, "sb16-worksheet.md"))
        self.assertIn("| Row 2 Family name or surname | [ask user] |", ws)
        self.assertIn("| Row 1 Family name or surname | Rider |", ws)
        self.assertIn("| Signature | leave blank", ws)
        self.assertIn("37 CFR 1.4(d)(2)", ws)
        self.assertNotIn("/Jane Q. Rider/", ws)          # never types an S-signature
        self.assertIn("| Applicant certifies micro entity status (attach PTO/SB/15A or 15B) | [x] check |", ws)
        self.assertIn("open-items", [f["code"] for f in res["findings"]])
        self.assertFalse(res["ok"])                       # required values still missing

    def test_ads_and_web_ads_worksheets(self):
        fill_forms.operate("worksheet", "ads", FILING, self.tmp)
        ws = read(os.path.join(self.tmp, "aia14-worksheet.md"))
        web = read(os.path.join(self.tmp, "web-ads-worksheet.md"))
        self.assertIn("## Inventor Information - Inventor 2", ws)
        self.assertIn("| Mailing Address: Address 1 | [ask user] |", ws)
        self.assertIn("| Application Type | Provisional |", ws)
        self.assertLess(web.index("Correspondence Information (QSG 3.2)"), web.index("Applicant Information (QSG 3.9)"))
        self.assertLess(web.index("Publication Information"), web.index("Domestic Benefit"))
        self.assertIn("never filled", web)
        self.assertNotIn("/Jane Q. Rider/", ws + web)

    def test_declaration_one_per_inventor(self):
        res = fill_forms.operate("worksheet", "AIA01", FILING, self.tmp)
        names = sorted(os.path.basename(p) for p in res["worksheets"])
        self.assertEqual(names, ["aia01-inventor1-worksheet.md", "aia01-inventor2-worksheet.md"])
        ws2 = read(os.path.join(self.tmp, "aia01-inventor2-worksheet.md"))
        self.assertIn("| Legal name of inventor | [ask user] |", ws2)

    def test_ids_in_provisional_blocks_and_rows_listed(self):
        ids = {"schema": "patentassist/ids@1", "sections": {
            "us_patents": [{"cite_no": 1, "document_number": "US-9,457,709-B2", "issue_date_form": "10-04-2016",
                            "patentee": "Smith"}],
            "us_publications": [], "foreign": [], "npl": [{"cite_no": 2, "citation": "Doe, Lights, 2019"}]}}
        ip = os.path.join(self.tmp, "ids.json")
        with open(ip, "w", encoding="utf-8") as fh:
            json.dump(ids, fh)
        res = fill_forms.operate("worksheet", "SB08", FILING, self.tmp, ids_path=ip)
        self.assertIn("ids-in-provisional", [f["code"] for f in res["findings"] if f["level"] == "BLOCK"])
        ws = read(os.path.join(self.tmp, "sb08-worksheet.md"))
        self.assertIn("US-9,457,709-B2", ws)
        self.assertIn("Doe, Lights, 2019", ws)

    def test_all_skips_irrelevant_forms(self):
        res = fill_forms.operate("worksheet", "all", FILING, self.tmp)
        self.assertIn("SB16", res["forms"])
        self.assertIn("SB15A", res["forms"])
        self.assertNotIn("SB15B", res["forms"])           # gross-income basis
        self.assertNotIn("SB08", res["forms"])            # provisional: no IDS
        self.assertNotIn("AIA82", res["forms"])           # no representative

    def test_bad_schema(self):
        p = os.path.join(self.tmp, "filing.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump({"schema": "patentassist/filing@2"}, fh)
        with self.assertRaises(fill_forms.UsageError):
            fill_forms.operate("worksheet", "SB16", p, self.tmp)

    def test_unknown_form(self):
        with self.assertRaises(fill_forms.UsageError):
            fill_forms.canonical_form("PTO/SB/99")


@unittest.skipUnless(HAVE_PYPDF and HAVE_RL, "pypdf and reportlab needed")
class FillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pa-forms-test-")
        self.acro = os.path.join(self.tmp, "acro.pdf")
        self.xfa = os.path.join(self.tmp, "xfa.pdf")
        make_acroform(self.acro)
        make_xfa(self.xfa)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_pdf_kind(self):
        self.assertEqual(fill_forms.pdf_kind(self.acro)[0], "acroform")
        self.assertEqual(fill_forms.pdf_kind(self.xfa)[0], "xfa")

    def test_fill_acroform_values_persist_signature_blank(self):
        out = os.path.join(self.tmp, "out")
        res = fill_forms.operate("fill", "SB16", FILING, out, pdf=self.acro)
        self.assertEqual(len(res["filled"]), 1)
        self.assertEqual(res["filled"][0]["lost"], [])
        self.assertTrue(os.path.exists(os.path.join(out, "sb16-worksheet.md")), "worksheet always written")
        from pypdf import PdfReader
        fields = PdfReader(res["filled"][0]["path"]).get_fields()
        self.assertEqual(fields["TITLE OF THE INVENTION 500 characters maxRow1"]["/V"],
                         "Helmet Turn-Signal System With Wireless Handlebar Remote")
        self.assertEqual(fields["Family Name or SurnameRow1"]["/V"], "Rider")
        self.assertEqual(fields["TYPED OR PRINTED NAME"]["/V"], "Jane Q. Rider")
        self.assertIn(str(fields["ME"].get("/V")), ("/Yes", "/On"))
        self.assertIn(fields["signature"].get("/V"), (None, ""))     # never filled
        self.assertIn(fields["DATE"].get("/V"), (None, ""))           # signer dates it
        self.assertIn("field-missing", [f["code"] for f in res["findings"]])  # small form lacks some SB/16 fields

    def test_fill_refuses_signature_even_if_mapped(self):
        findings = []
        out = os.path.join(self.tmp, "x.pdf")
        fill_forms.fill_pdf(self.acro, out, {"signature": "/Jane Q. Rider/", "DOCKET NUMBER": "D-1"}, findings, "t")
        from pypdf import PdfReader
        fields = PdfReader(out).get_fields()
        self.assertIn(fields["signature"].get("/V"), (None, ""))
        self.assertEqual(fields["DOCKET NUMBER"]["/V"], "D-1")

    def test_xfa_not_filled_worksheet_written(self):
        out = os.path.join(self.tmp, "out")
        res = fill_forms.operate("fill", "AIA14", FILING, out, pdf=self.xfa)
        self.assertEqual(res["filled"], [])
        self.assertEqual(res["pdf_kind"], "xfa")
        self.assertIn("xfa-not-filled", [f["code"] for f in res["findings"]])
        ws = read(os.path.join(out, "aia14-worksheet.md"))
        self.assertIn("NOT filled", ws)
        self.assertTrue(os.path.exists(os.path.join(out, "web-ads-worksheet.md")))


if __name__ == "__main__":
    unittest.main()


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


class ProSeAndTranslationTest(unittest.TestCase):
    """F40: a pro se inventor was asked for a registration number. ids.py renamed the IDS column
    translation -> non_english and added translation_attached (the SB/08 "T" box)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_reg_no_left_blank_for_pro_se_inventor(self):
        res = fill_forms.operate("worksheet", "SB16", FILING, self.tmp, role="inventor")
        ws = read(os.path.join(self.tmp, "sb16-worksheet.md"))
        self.assertIn("leave blank (not a practitioner)", ws)
        line = [l for l in ws.splitlines() if "Registration No" in l][0]
        self.assertNotIn("[ask user]", line)
        vals = fill_forms.values_from_lines(fill_forms.map_sb16(dict(load(FILING), _profile_role="inventor")))
        self.assertNotIn("REGISTRATION NO", vals)       # never typed into the PDF
        self.assertGreaterEqual(res["summary"]["open_required"], 0)

    def test_reg_no_still_asked_for_an_attorney(self):
        fill_forms.operate("worksheet", "SB16", FILING, self.tmp, role="attorney")
        ws = read(os.path.join(self.tmp, "sb16-worksheet.md"))
        line = [l for l in ws.splitlines() if "Registration No" in l][0]
        self.assertIn("[ask user]", line)

    def test_role_read_from_state_json(self):
        d = os.path.join(self.tmp, "patent")
        os.makedirs(os.path.join(d, "draft"))
        shutil.copy(FILING, os.path.join(d, "draft", "filing.json"))
        with open(os.path.join(d, "state.json"), "w") as fh:
            json.dump({"schema": "patentassist/state@1", "profile": {"role": "inventor"}}, fh)
        res = fill_forms.run({"command": "worksheet", "form": "SB16", "dir": d, "no_audit": True})
        self.assertIn("leave blank (not a practitioner)", read(res["worksheets"][0]))

    def test_sb08_t_box_means_translation_attached(self):
        f = dict(load(FILING), filing_type="nonprovisional")
        ids = {"schema": "patentassist/ids@1", "sections": {"us_patents": [], "us_publications": [], "npl": [],
               "foreign": [{"cite_no": 1, "document_number": "EP-0944293-A1", "publication_date_form": "09-22-1999",
                            "applicant": "Gaggenau", "non_english": True, "translation_attached": False},
                           {"cite_no": 2, "document_number": "JP-S63269488-A", "publication_date_form": "11-07-1988",
                            "applicant": "Matsushita", "non_english": True, "translation_attached": True},
                           {"cite_no": 3, "document_number": "DE-3146638-A1", "publication_date_form": "06-01-1983",
                            "applicant": "X", "translation": True}]}}   # old column name: not a T tick
        lines, rows = fill_forms.map_sb08(f, ids)
        self.assertEqual([r[5] for r in rows["foreign"]], [False, True, False])
        txt = "\n".join(l.shown() for l in lines)
        self.assertIn("T box: tick (English translation attached)", txt)
        self.assertIn("concise explanation of relevance", txt)
