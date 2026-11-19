#!/usr/bin/env python3
"""fill_forms.py - USPTO form worksheets, and AcroForm filling where the PDF allows it.

Usage:
  python3 scripts/fill_forms.py worksheet FORM --filing draft/filing.json --out draft/out/
  python3 scripts/fill_forms.py fill FORM --filing draft/filing.json --pdf path/to/blank.pdf --out draft/out/
  FORM: SB16 | AIA14 | AIA01 | SB15A | SB15B | AIA82 | SB08 | all (worksheet only)
  common options: [--ids draft/out/ids.json] [--dir patent] [--json] [--no-audit]

What it does
  * worksheet: a Markdown sheet listing every section/line of the form in form order with the exact
    value to type, "[ask user]" where filing.json has null, and "leave blank" for signature lines.
    Registration numbers read "leave blank (not a practitioner)" when filing.json has no representative
    and state.json profile.role is inventor (a pro se filer has no registration number).
    SB08: the "T" box is ticked only when ids.json says translation_attached is true.
    AIA14 also gets web-ads-worksheet.md (Patent Center Web ADS, same data, in the order of the
    Web ADS Quick Start Guide sections 3.1-3.13).
  * fill: always writes the worksheet first. Then, if the blank PDF is a real AcroForm (field widgets,
    no dynamic-XFA-only layout), fills it with pypdf, re-reads the output and confirms every value
    persisted. Dynamic XFA forms (NeedsRendering / no AcroForm fields), such as the current ADS
    PTO/AIA/14 (03-26) and the Patent Center "auto-load" SB/16 and SB/08, are never filled.
  * Signature fields are never filled and never mapped. Each signer types their own S-signature
    between slashes, e.g. /Jane Q. Doe/ (37 CFR 1.4(d)(2)). Execution dates are left for the signer.
    Certification text on USPTO forms is never edited (37 CFR 1.4(d)(6)).

Form status (checked 2026-11-18 with pypdf 6.9.2 on PDFs from uspto.gov; see references/forms-and-filing.md):
  AcroForm: sb0016.pdf (SB/16 01-25), aia0001.pdf (AIA/01), sb0015a.pdf, sb0015b.pdf, aia0082.pdf
            (AIA/82A+82B), sb0008a.pdf (SB/08a; NPL goes on SB/08b - worksheet only here)
  Dynamic XFA (worksheet only): aia0014.pdf / aia0014pc.pdf (ADS), sb0016pc.pdf, sb0008pc.pdf

filing.json (patentassist/filing@1) fields read by this script. Every value comes from the user;
null means "not given yet" and is shown as [ask user]; false means "no".
  filing_type        "provisional" | "nonprovisional" | "nonprovisional_claiming_priority"
  title, attorney_docket, application_number, filing_date (YYYY-MM-DD), art_unit, examiner
  inventors[]        {prefix, given, middle, family, suffix,
                      residence: {city, state, country, military},
                      mailing: {address1, address2, city, state, postcode, country}, email, phone}
  applicants[]       empty/absent = the inventors are the applicant. Otherwise
                      {kind: assignee|obligated_assignee|proprietary_interest|legal_representative|joint_inventor,
                       org_name | {given, middle, family}, address: {...}, email, phone}
  assignees[]        non-applicant assignees to print on the publication (same shape as applicants)
  correspondence     {customer_no} or {name, name2, address: {...}, email, phone, fax}
  entity_status      "large" | "small" | "micro";  micro_basis: "gross_income" | "higher_education"
  domestic_benefit[] {prior_app_no, prior_filing_date, relationship ("claims benefit of provisional",
                      "continuation of", ...), status ("pending"|"patented"|"abandoned"|"expired"),
                      patent_number, issue_date}
  foreign_priority[] {app_no, country, filing_date, access_code}
  government_interest {funded: bool, made_by_agency: bool, agency, contract_no}
  representative     {customer_no, practitioners: [{given, family, reg_no}]}
  nonpublication_request, early_publication, pdx_opt_out, epo_search_opt_out, secrecy_order (bools)
  ads_enclosed (bool), drawing_sheets, spec_pages, suggested_figure, other_enclosures, total_fee
  signer             {given, middle, family, reg_no, phone, title}  (typed name only, never the signature)
Exit codes: 0 ok, 1 required values missing (worksheet still written), 2 usage/input error.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

ASK = "[ask user]"
SIG_NOTE = ("leave blank - the signer types their own S-signature between slashes, e.g. /Jane Q. Doe/ "
            "(37 CFR 1.4(d)(2)); never typed by this tool")
DATE_NOTE = "leave blank - the signer dates it when signing"
SIG_RE = re.compile(r"(^|[^a-z])sign(ature)?([^a-z]|$)", re.I)   # 'Signature', 'Sign' - not 'Assignee'

FORMS = {
    "SB16": {"title": "PTO/SB/16 Provisional Application for Patent Cover Sheet", "file": "sb0016.pdf"},
    "AIA14": {"title": "PTO/AIA/14 Application Data Sheet (37 CFR 1.76)", "file": "aia0014pc.pdf"},
    "AIA01": {"title": "PTO/AIA/01 Declaration (37 CFR 1.63) for Utility or Design Application Using an ADS",
              "file": "aia0001.pdf"},
    "SB15A": {"title": "PTO/SB/15A Certification of Micro Entity Status (Gross Income Basis)", "file": "sb0015a.pdf"},
    "SB15B": {"title": "PTO/SB/15B Certification of Micro Entity Status (Institution of Higher Education Basis)",
              "file": "sb0015b.pdf"},
    "AIA82": {"title": "PTO/AIA/82A Transmittal for Power of Attorney + PTO/AIA/82B Power of Attorney",
              "file": "aia0082.pdf"},
    "SB08": {"title": "PTO/SB/08a Information Disclosure Statement by Applicant (NPL on SB/08b)",
             "file": "sb0008a.pdf"},
}
ALIASES = {"SB016": "SB16", "SB0016": "SB16", "PTO/SB/16": "SB16", "COVER": "SB16",
           "AIA014": "AIA14", "AIA0014": "AIA14", "ADS": "AIA14", "PTO/AIA/14": "AIA14",
           "AIA001": "AIA01", "AIA0001": "AIA01", "DECLARATION": "AIA01", "PTO/AIA/01": "AIA01",
           "SB015A": "SB15A", "SB0015A": "SB15A", "SB015B": "SB15B", "SB0015B": "SB15B",
           "AIA082": "AIA82", "AIA0082": "AIA82", "POA": "AIA82", "PTO/AIA/82": "AIA82",
           "SB008": "SB08", "SB0008": "SB08", "SB08A": "SB08", "SB0008A": "SB08", "IDS": "SB08", "PTO/SB/08": "SB08"}


class UsageError(Exception):
    pass


# --------------------------------------------------------------------------- data helpers

def g(d: Any, path: str, default=None):
    """Dotted get that tolerates missing levels: g(f, 'correspondence.address.city')."""
    cur = d
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return default
        if cur is None:
            return default
    return cur


def full_name(p: Optional[dict]) -> Optional[str]:
    if not p:
        return None
    if p.get("org_name"):
        return p["org_name"]
    parts = [p.get("prefix"), p.get("given"), p.get("middle"), p.get("family"), p.get("suffix")]
    if not p.get("given") or not p.get("family"):
        return None
    return " ".join(str(x) for x in parts if x)


def given_middle(p: dict) -> Optional[str]:
    if not p.get("given"):
        return None
    return " ".join(str(x) for x in (p.get("given"), p.get("middle")) if x)


def residence_line(p: dict) -> Optional[str]:
    r = p.get("residence") or {}
    if r.get("military"):
        return "Active US Military Service"
    if not r.get("city") or not r.get("country"):
        return None
    if str(r.get("country")).upper() in ("US", "USA", "UNITED STATES"):
        return "%s, %s" % (r["city"], r["state"]) if r.get("state") else None
    return "%s, %s" % (r["city"], r["country"])


def addr_line(a: Optional[dict]) -> Optional[str]:
    if not a:
        return None
    s = ", ".join(str(x) for x in (a.get("address1"), a.get("address2")) if x)
    return s or None


def fmt_date(iso: Optional[str], style: str = "iso") -> Optional[str]:
    if not iso:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(iso))
    if not m:
        return str(iso)
    y, mo, d = m.groups()
    return "%s/%s/%s" % (mo, d, y) if style == "us" else "%s-%s-%s" % (y, mo, d)


def yes(v) -> Optional[bool]:
    return None if v is None else bool(v)


# --------------------------------------------------------------------------- worksheet model

class Line:
    """One form line. kind: text | check | signature | date_sig | info | blank (an instruction to leave the
    field empty, never typed into the PDF)."""
    __slots__ = ("section", "label", "value", "field", "kind", "note", "required", "on")

    def __init__(self, section, label, value, field=None, kind="text", note="", required=False, on=None):
        self.section, self.label, self.value, self.field = section, label, value, field
        self.kind, self.note, self.required, self.on = kind, note, required, on

    def shown(self) -> str:
        if self.kind == "signature":
            return SIG_NOTE
        if self.kind == "date_sig":
            return DATE_NOTE
        if self.kind == "check":
            if self.value is None:
                return ASK
            return "[x] check" if self.value else "[ ] leave unchecked"
        if self.kind in ("info", "blank"):
            return str(self.value) if self.value is not None else ""
        if self.value is None:
            return ASK
        if self.value == "":
            return "(leave blank)"
        return str(self.value)


NOT_PRACTITIONER = "leave blank (not a practitioner)"


def pro_se(f: dict) -> bool:
    """No representative in filing.json and state.json profile.role is inventor: nobody signing is a
    registered practitioner, so registration-number fields are left blank, not asked for (F40)."""
    rep = f.get("representative")
    has_rep = isinstance(rep, dict) and (rep.get("customer_no") or rep.get("practitioners"))
    return not has_rep and str(f.get("_profile_role") or "").lower() == "inventor"


def reg_no_line(S, label, f, signer, field=None, note=""):
    if signer.get("reg_no") is None and pro_se(f):
        return Line(S, label, NOT_PRACTITIONER, field, "blank")
    return Line(S, label, signer.get("reg_no"), field, note=note)


# --------------------------------------------------------------------------- per-form mappings

def map_sb16(f: dict) -> List[Line]:
    L = []
    S = "Inventor(s)"
    invs = f.get("inventors") or []
    if not invs:
        L.append(Line(S, "Inventor 1 legal name", None, required=True))
    for i, inv in enumerate(invs[:5], start=1):
        L.append(Line(S, "Row %d Given name (first and middle)" % i, given_middle(inv),
                      "Given Name first and middle if anyRow%d" % i, required=True))
        L.append(Line(S, "Row %d Family name or surname" % i, inv.get("family"),
                      "Family Name or SurnameRow%d" % i, required=True))
        L.append(Line(S, "Row %d Residence (city and state or foreign country)" % i, residence_line(inv),
                      "Residence City and either State or Foreign CountryRow%d" % i, required=True))
    if len(invs) > 5:
        L.append(Line(S, "Additional inventors named on separately numbered sheets (count)", None,
                      "Additional inventors are being named on the",
                      note="%d more inventors: attach numbered sheet(s) listing them" % (len(invs) - 5),
                      required=True))
    L.append(Line("Title of the invention (500 characters max)", "Title", f.get("title"),
                  "TITLE OF THE INVENTION 500 characters maxRow1", required=True))
    S = "Correspondence address"
    cust = g(f, "correspondence.customer_no")
    L.append(Line(S, "The address corresponding to Customer Number", True if cust else False,
                  "The address corresponding to Customer Number", "check"))
    L.append(Line(S, "Customer Number", cust if cust else ("" if g(f, "correspondence.address") else None),
                  "CORRESPONDENCE ADDRESS", note="" if cust else "not used when an address is given below",
                  required=not g(f, "correspondence.address")))
    use_addr = not cust
    L.append(Line(S, "Firm or Individual Name (checkbox)", True if use_addr else False, "undefined", "check"))
    if use_addr:
        L.append(Line(S, "Firm or Individual Name", g(f, "correspondence.name"), "Firm or Individual Name", required=True))
        L.append(Line(S, "Address", addr_line(g(f, "correspondence.address")), "Address", required=True))
        L.append(Line(S, "City", g(f, "correspondence.address.city"), "City", required=True))
        L.append(Line(S, "State", g(f, "correspondence.address.state"), "State"))
        L.append(Line(S, "Zip", g(f, "correspondence.address.postcode"), "zip code", required=True))
        L.append(Line(S, "Country", g(f, "correspondence.address.country"), "Country", required=True))
        L.append(Line(S, "Telephone", g(f, "correspondence.phone"), "Telephone_2"))
        L.append(Line(S, "Email", g(f, "correspondence.email"), "Email_2"))
    S = "Enclosed application parts (check all that apply)"
    ads = yes(f.get("ads_enclosed"))
    L.append(Line(S, "Application Data Sheet (37 CFR 1.76)", ads if ads is not None else False, "ADS checkbox", "check"))
    L.append(Line(S, "Specification (e.g., description of the invention)", True,
                  "Specification eg description of the invention", "check"))
    L.append(Line(S, "Number of pages (specification)", f.get("spec_pages"), "Number of Pages",
                  note="build_docx.py --pdf-check counts them"))
    sheets = f.get("drawing_sheets")
    L.append(Line(S, "Drawing(s)", None if sheets is None else bool(sheets), "Drawings", "check"))
    L.append(Line(S, "Number of sheets (drawings)", sheets if sheets else ("" if sheets == 0 else None),
                  "Number of Sheets", note="drawings-manifest.json lists the sheets"))
    L.append(Line(S, "CD(s), Number of CDs", False, "CD(s)", "check"))
    other = f.get("other_enclosures")
    L.append(Line(S, "Other (specify)", bool(other) if other is not None else False, "Other specify", "check"))
    if other:
        L.append(Line(S, "Other enclosures", other, "undefined_2"))
    S = "Fees"
    ent = f.get("entity_status")
    L.append(Line(S, "Applicant asserts small entity status (37 CFR 1.27)", None if ent is None else ent == "small",
                  "SE", "check", required=True))
    L.append(Line(S, "Applicant certifies micro entity status (attach PTO/SB/15A or 15B)",
                  None if ent is None else ent == "micro", "ME", "check", required=True))
    L.append(Line(S, "Method of payment", "pay online in Patent Center (leave the check / money order / credit card / "
                                          "deposit account boxes unchecked)", kind="info"))
    L.append(Line(S, "TOTAL FEE AMOUNT ($)", f.get("total_fee"), "TOTAL FEE AMOUNT", note="from fees.py"))
    S = "U.S. Government interest (page 2)"
    gi = f.get("government_interest") or {}
    funded = gi.get("funded")
    by_agency = gi.get("made_by_agency")
    L.append(Line(S, "No. (not made by or under contract with a US Government agency)",
                  None if funded is None and by_agency is None else not (funded or by_agency), "No", "check",
                  required=True))
    L.append(Line(S, "Yes, made by an agency of the US Government", None if by_agency is None else bool(by_agency),
                  "Yes the invention was made by an agency of the US Government The US Government agency name is",
                  "check"))
    if by_agency:
        L.append(Line(S, "Agency name (made by an agency)", gi.get("agency"), "undefined_3", required=True))
    L.append(Line(S, "Yes, made under a contract with a US Government agency", None if funded is None else bool(funded),
                  "Yes the invention was made under a contract with an agency of the US Government", "check"))
    if funded:
        L.append(Line(S, "The contract number is", gi.get("contract_no"), "The contract number is", required=True))
        L.append(Line(S, "The US Government agency name is", gi.get("agency"), "The US Government agency name is",
                      required=True))
    S = "Signature block (page 2)"
    signer = f.get("signer") or {}
    L.append(Line(S, "Signature", None, "signature", "signature"))
    L.append(Line(S, "Date", None, "DATE", "date_sig"))
    L.append(Line(S, "Typed or printed name", full_name(signer), "TYPED OR PRINTED NAME", required=True))
    L.append(reg_no_line(S, "Registration No. (if appropriate)", f, signer, "REGISTRATION NO",
                         note="leave blank if the signer is not a practitioner"))
    L.append(Line(S, "Telephone", signer.get("phone"), "TELEPHONE"))
    L.append(Line(S, "Docket number", f.get("attorney_docket"), "DOCKET NUMBER"))
    return L


def map_aia01(f: dict, inv: dict, idx: int) -> List[Line]:
    L = []
    S = "Declaration (inventor %d)" % idx
    L.append(Line(S, "Title of invention", f.get("title"), "Title of Invention", required=True))
    appno = f.get("application_number")
    L.append(Line(S, "This declaration is directed to: the attached application", not bool(appno),
                  "This declaration", "check"))
    L.append(Line(S, "This declaration is directed to: United States application or PCT international application",
                  bool(appno), "undefined", "check"))
    if appno:
        L.append(Line(S, "Application number", appno, "United States application or PCT international application number"))
        L.append(Line(S, "Filed on", fmt_date(f.get("filing_date"), "us"), "filed on"))
    L.append(Line(S, "Statements", "printed on the form (believed original inventor; 18 U.S.C. 1001 warning) - "
                                   "do not edit (37 CFR 1.4(d)(6))", kind="info"))
    L.append(Line(S, "Legal name of inventor", full_name(inv), "Inventor", required=True))
    L.append(Line(S, "Date (optional)", None, "Date Optional", "date_sig"))
    L.append(Line(S, "Signature", None, "Text4", "signature"))
    L.append(Line(S, "Note", "file one AIA/01 per inventor; it may be postponed until the issue fee is paid if the ADS "
                             "gives each inventor's legal name, residence and mailing address (37 CFR 1.53(f)(3)), "
                             "but the 1.16(f) surcharge then applies", kind="info"))
    return L


def map_sb15(f: dict, form: str) -> List[Line]:
    L = []
    S = "Header"
    invs = f.get("inventors") or []
    L.append(Line(S, "Application Number or Control Number (if applicable)", f.get("application_number") or "",
                  "Application Number or Control Number if applicable",
                  note="blank when filed with a new application"))
    L.append(Line(S, "Patent Number (if applicable)", "", "Patent Number if applicable"))
    L.append(Line(S, "First Named Inventor", full_name(invs[0]) if invs else None, "First Named Inventor", required=True))
    L.append(Line(S, "Title of Invention", f.get("title"), "Title of Invention", required=True))
    L.append(Line("Certification", "Certification statements",
                  "printed on the form - every signer must personally meet them; do not edit (37 CFR 1.4(d)(6)); "
                  "check eligibility first (references/entity-status.md; 37 CFR 1.29(a) gross income or 1.29(d) "
                  "higher education)", kind="info"))
    signer = f.get("signer") or {}
    blocks = [("", "")] if form == "SB15A" else [("", ""), ("_2", " (second block)")]
    for suf, lab in blocks:
        S = "Signature block%s" % lab
        L.append(Line(S, "Signature", None, "Signature" + suf, "signature"))
        L.append(Line(S, "Name", full_name(signer) if not suf else None, "Name" + suf,
                      required=not suf, note="each applicant/inventor signs (own form or own block)"))
        L.append(Line(S, "Date", None, "Date" + suf, "date_sig"))
        L.append(Line(S, "Telephone", signer.get("phone") if not suf else None, "Telephone" + suf))
        if suf:
            L.append(Line(S, "Registration No.", None, "Registration No" + suf, note="only for a practitioner signer"))
        else:
            L.append(reg_no_line(S, "Registration No.", f, signer, "Registration No", note="only for a practitioner signer"))
    n = len(invs)
    L.append(Line("Multiple forms", "More than one form is being submitted", n > 1 if invs else None,
                  "Check Box2" if form == "SB15A" else "Check Box3", "check",
                  note="each inventor/applicant must sign a certification"))
    return L


def map_aia82(f: dict) -> List[Line]:
    L = []
    invs = f.get("inventors") or []
    signer = f.get("signer") or {}
    apps = f.get("applicants") or []
    juristic = next((a for a in apps if a.get("org_name")), None)
    S = "PTO/AIA/82A Transmittal (page 1)"
    L.append(Line(S, "Application Number", f.get("application_number") or "", "Application Number",
                  note="blank when filed with a new application"))
    L.append(Line(S, "Filing Date", fmt_date(f.get("filing_date"), "us") or "", "Filing Date"))
    L.append(Line(S, "First Named Inventor", full_name(invs[0]) if invs else None, "First Named Inventor", required=True))
    L.append(Line(S, "Title", f.get("title"), "Title", required=True))
    L.append(Line(S, "Art Unit", f.get("art_unit") or "", "Art Unit"))
    L.append(Line(S, "Examiner Name", f.get("examiner") or "", "Examiner Name"))
    L.append(Line(S, "Attorney Docket Number", f.get("attorney_docket") or "", "Attorney Docket Number"))
    L.append(Line(S, "Signature", None, "Signature", "signature"))
    L.append(Line(S, "Date (optional)", None, "Date Optional", "date_sig"))
    L.append(Line(S, "Name", full_name(signer), "Name", required=True))
    L.append(Line(S, "Registration Number", signer.get("reg_no") or "", "Registration Number"))
    L.append(Line(S, "Title (if applicant is a juristic entity)", signer.get("title") if juristic else "",
                  "Title if Applicant is a juristic entity", required=bool(juristic)))
    L.append(Line(S, "Applicant Name (if applicant is a juristic entity)", juristic.get("org_name") if juristic else "",
                  "Applicant Name if Applicant is a juristic entity"))
    S = "PTO/AIA/82B Power of Attorney (page 2)"
    rep = f.get("representative") or {}
    cust = rep.get("customer_no")
    pr = rep.get("practitioners") or []
    L.append(Line(S, "Appoint the practitioners associated with Customer Number", bool(cust) if (cust or pr) else None,
                  "Appoint attorneys listed under customer number", "check", required=True))
    L.append(Line(S, "Customer Number", cust or "", "Customer Number"))
    L.append(Line(S, "Appoint the practitioners named in the attached list (page 3)", bool(pr) and not cust,
                  "Appoint attorneys listed on the attached list", "check"))
    ccust = g(f, "correspondence.customer_no")
    L.append(Line(S, "Correspondence: the address associated with the above Customer Number",
                  bool(cust and ccust and str(ccust) == str(cust)),
                  "The address with the above mentioned customer number", "check"))
    L.append(Line(S, "Correspondence: the address associated with Customer Number",
                  bool(ccust and str(ccust) != str(cust)), "The address associated with customer number", "check"))
    L.append(Line(S, "Correspondence Customer Number", ccust if ccust and str(ccust) != str(cust) else "",
                  "Customer Number2"))
    use_addr = not ccust
    L.append(Line(S, "Correspondence: Firm or Individual Name", use_addr, "Box for Firm or Individual Name", "check"))
    if use_addr:
        L.append(Line(S, "Firm or Individual Name", g(f, "correspondence.name"), "Firm or Individual Name", required=True))
        L.append(Line(S, "Address", addr_line(g(f, "correspondence.address")), "Street Address", required=True))
        L.append(Line(S, "City", g(f, "correspondence.address.city"), "City", required=True))
        L.append(Line(S, "State", g(f, "correspondence.address.state"), "State_2"))
        L.append(Line(S, "Zip", g(f, "correspondence.address.postcode"), "Zip", required=True))
        L.append(Line(S, "Country", g(f, "correspondence.address.country"), "Country"))
        L.append(Line(S, "Telephone", g(f, "correspondence.phone"), "Telephone Number"))
        L.append(Line(S, "Email", g(f, "correspondence.email"), "Email Address"))
    L.append(Line(S, "Applicant Name (if juristic entity)", juristic.get("org_name") if juristic else "",
                  "Applicant Name (if applicant is a juristic entity)"))
    kind = (apps[0].get("kind") if apps else "inventor")
    L.append(Line(S, "Applicant is: Inventor or Joint Inventor", kind in ("inventor", "joint_inventor"),
                  "Inventor or Joint inventor", "check"))
    L.append(Line(S, "Applicant is: Legal Representative of a deceased or legally incapacitated inventor",
                  kind == "legal_representative",
                  "Legal Representative of a deceased or legally incapacitated inventor", "check"))
    L.append(Line(S, "Applicant is: Assignee or person to whom the inventor is under an obligation to assign",
                  kind in ("assignee", "obligated_assignee"), "Assignee", "check"))
    L.append(Line(S, "Applicant is: Person who otherwise shows sufficient proprietary interest",
                  kind == "proprietary_interest", "Person who otherwise sufficient proprietary interest", "check"))
    L.append(Line(S, "Signature of applicant", None, "Signature of the applicant for patent", "signature"))
    L.append(Line(S, "Date (optional)", None, "Date Optional_2", "date_sig"))
    L.append(Line(S, "Name of signer", full_name(signer), "Name of the Signer", required=True))
    L.append(Line(S, "Title of signer (juristic entity)", signer.get("title") if juristic else "", "Title of the Signer"))
    if pr and not cust:
        S = "Practitioner list (page 3)"
        for i, p in enumerate(pr[:10], start=1):
            L.append(Line(S, "Name %d" % i, full_name(p), "NameRow%d" % i, required=True))
            L.append(Line(S, "Registration Number %d" % i, p.get("reg_no"), "Registration NumberRow%d" % i,
                          required=True))
    return L


def map_sb08(f: dict, ids: Optional[dict]) -> Tuple[List[Line], dict]:
    """Header lines + citation rows (filled later by geometry). Returns (lines, rows)."""
    L = []
    invs = f.get("inventors") or []
    S = "Header (complete if known)"
    L.append(Line(S, "Application Number", f.get("application_number"), "text3", required=True))
    L.append(Line(S, "Filing Date", fmt_date(f.get("filing_date"), "us"), "text4", required=True))
    L.append(Line(S, "First Named Inventor", full_name(invs[0]) if invs else None, "text5", required=True))
    L.append(Line(S, "Art Unit", f.get("art_unit"), "text6"))
    L.append(Line(S, "Examiner Name", f.get("examiner"), "text7"))
    L.append(Line(S, "Attorney Docket Number", f.get("attorney_docket") or "", "text8"))
    rows = {"us": [], "foreign": [], "npl": []}
    if ids:
        sec = ids.get("sections") or {}
        for r in (sec.get("us_patents") or []):
            rows["us"].append([str(r.get("cite_no") or ""), r.get("document_number"), r.get("issue_date_form"),
                               r.get("patentee"), r.get("pages") or ""])
        for r in (sec.get("us_publications") or []):
            rows["us"].append([str(r.get("cite_no") or ""), r.get("document_number"), r.get("publication_date_form"),
                               r.get("applicant"), r.get("pages") or ""])
        for r in (sec.get("foreign") or []):
            # SB/08 "T" box = an English translation is ATTACHED (ids.py translation_attached), not "the
            # document is non-English" (ids.py non_english). Older ids.json files had neither.
            rows["foreign"].append([str(r.get("cite_no") or ""), r.get("document_number"),
                                    r.get("publication_date_form"), r.get("applicant"), r.get("pages") or "",
                                    r.get("translation_attached") is True])
            rows.setdefault("foreign_non_english", []).append(bool(r.get("non_english")))
        for r in (sec.get("npl") or []):
            rows["npl"].append([str(r.get("cite_no") or ""), r.get("citation")])
    for r in rows["us"]:
        L.append(Line("U.S. Patent Documents", "Cite %s" % r[0],
                      "%s | date %s | %s | %s" % (r[1] or ASK, r[2] or ASK, r[3] or ASK, r[4] or "-")))
    for i, r in enumerate(rows["foreign"]):
        ne = (rows.get("foreign_non_english") or [False] * len(rows["foreign"]))[i]
        t_box = ("T box: tick (English translation attached)" if r[5] else
                 "T box: leave unticked (no translation attached)" +
                 ("; non-English: give a concise explanation of relevance (37 CFR 1.98(a)(3))" if ne else ""))
        L.append(Line("Foreign Patent Documents", "Cite %s" % r[0],
                      "%s | date %s | %s | %s | %s" % (r[1] or ASK, r[2] or ASK, r[3] or ASK, r[4] or "-", t_box)))
    for r in rows["npl"]:
        L.append(Line("Non-Patent Literature (PTO/SB/08b - not filled here)", "Cite %s" % r[0], r[1]))
    if not ids:
        L.append(Line("Citations", "Reference list", None,
                      note="run ids.py to write draft/out/ids.json (verified references only)", required=True))
    L.append(Line("Examiner block", "Examiner signature / date considered", "leave blank - examiner only", kind="info"))
    L.append(Line("Size fee", "IDS size-fee assertion (37 CFR 1.98(a)(4), 1.17(v))",
                  "SB/08a has no size-fee assertion: add PTO/SB/08c, or use the Patent Center auto-load SB/08 "
                  "(XFA) in Adobe Reader", kind="info"))
    return L, rows


def map_aia14(f: dict) -> List[Line]:
    """ADS lines in the order of the PDF form (PTO/AIA/14 03-26 XFA template)."""
    L = []
    invs = f.get("inventors") or []
    S = "Header"
    L.append(Line(S, "Attorney Docket Number", f.get("attorney_docket") or ""))
    L.append(Line(S, "Application Number", f.get("application_number") or "", note="blank for a new application"))
    L.append(Line(S, "Title of Invention", f.get("title"), required=True))
    L.append(Line("Secrecy Order 37 CFR 5.2", "Portions or all of the application may fall under a Secrecy Order",
                  yes(f.get("secrecy_order")) if f.get("secrecy_order") is not None else False, kind="check",
                  note="a secrecy-order application cannot be filed electronically"))
    if not invs:
        L.append(Line("Inventor Information", "Inventor 1", None, required=True))
    for i, inv in enumerate(invs, start=1):
        S = "Inventor Information - Inventor %d" % i
        L.append(Line(S, "Legal Name: Prefix", inv.get("prefix") or ""))
        L.append(Line(S, "Legal Name: Given Name", inv.get("given"), required=True))
        L.append(Line(S, "Legal Name: Middle Name", inv.get("middle") or ""))
        L.append(Line(S, "Legal Name: Family Name", inv.get("family"), required=True))
        L.append(Line(S, "Legal Name: Suffix", inv.get("suffix") or ""))
        r = inv.get("residence") or {}
        country = r.get("country")
        if r.get("military"):
            res = "Active US Military Service"
        elif country is None:
            res = None
        else:
            res = "US Residency" if str(country).upper() in ("US", "USA", "UNITED STATES") else "Non US Residency"
        L.append(Line(S, "Residence Information (select one)", res, required=True))
        L.append(Line(S, "Residence: City", r.get("city"), required=not r.get("military")))
        if res == "US Residency":
            L.append(Line(S, "Residence: State/Province", r.get("state"), required=True))
        L.append(Line(S, "Residence: Country of Residence", country, required=not r.get("military")))
        m = inv.get("mailing") or {}
        L.append(Line(S, "Mailing Address: Address 1", m.get("address1"), required=True))
        L.append(Line(S, "Mailing Address: Address 2", m.get("address2") or ""))
        L.append(Line(S, "Mailing Address: City", m.get("city"), required=True))
        L.append(Line(S, "Mailing Address: State/Province", m.get("state") or ""))
        L.append(Line(S, "Mailing Address: Postal Code", m.get("postcode"), required=True))
        L.append(Line(S, "Mailing Address: Country", m.get("country"), required=True))
    S = "Correspondence Information"
    c = f.get("correspondence") or {}
    cust = c.get("customer_no")
    L.append(Line(S, "Customer Number", cust or ("" if c.get("address") else None), required=not c.get("address")))
    L.append(Line(S, "An address is being provided for the correspondence information", not bool(cust), kind="check"))
    if not cust:
        L.append(Line(S, "Name 1", c.get("name"), required=True))
        L.append(Line(S, "Name 2", c.get("name2") or ""))
        L.append(Line(S, "Address 1", g(c, "address.address1"), required=True))
        L.append(Line(S, "Address 2", g(c, "address.address2") or ""))
        L.append(Line(S, "City", g(c, "address.city"), required=True))
        L.append(Line(S, "State/Province", g(c, "address.state") or ""))
        L.append(Line(S, "Country", g(c, "address.country"), required=True))
        L.append(Line(S, "Postal Code", g(c, "address.postcode"), required=True))
        L.append(Line(S, "Phone Number", c.get("phone") or ""))
        L.append(Line(S, "Fax Number", c.get("fax") or ""))
    L.append(Line(S, "Email Address", c.get("email"), required=True))
    S = "Application Information"
    L.append(Line(S, "Title of the Invention", f.get("title"), required=True))
    L.append(Line(S, "Attorney Docket Number", f.get("attorney_docket") or ""))
    ent = f.get("entity_status")
    L.append(Line(S, "Small Entity Status Claimed", None if ent is None else ent == "small", kind="check",
                  note="micro entity: leave unchecked and file PTO/SB/15A or 15B" if ent == "micro" else ""))
    ft = f.get("filing_type")
    L.append(Line(S, "Application Type", None if not ft else ("Provisional" if ft == "provisional" else "Nonprovisional"),
                  required=True))
    L.append(Line(S, "Subject Matter", "Utility"))
    L.append(Line(S, "Total Number of Drawing Sheets (if any)", f.get("drawing_sheets")))
    L.append(Line(S, "Suggested Figure for Publication (if any)",
                  f.get("suggested_figure") or ("" if ft == "provisional" else None)))
    S = "Filing By Reference (35 U.S.C. 111(c), 37 CFR 1.57(a))"
    L.append(Line(S, "Application number / filing date / IP authority", "",
                  note="leave blank - only for an application filed by reference instead of a specification"))
    S = "Publication Information"
    L.append(Line(S, "Request Early Publication (fee, 37 CFR 1.219)", yes(f.get("early_publication")) or False,
                  kind="check"))
    npr = f.get("nonpublication_request")
    L.append(Line(S, "Request Not to Publish (35 U.S.C. 122(b)(2)(B)(i))",
                  None if (npr is None and ft != "provisional") else bool(npr), kind="check",
                  note="only if the invention has not been and will not be the subject of an application filed "
                       "abroad; provisionals are never published"))
    S = "Representative Information"
    rep = f.get("representative") or {}
    if rep.get("customer_no"):
        L.append(Line(S, "Please Select One", "Customer Number"))
        L.append(Line(S, "Customer Number", rep["customer_no"]))
    elif rep.get("practitioners"):
        L.append(Line(S, "Please Select One", "US Patent Practitioner"))
        for i, p in enumerate(rep["practitioners"], start=1):
            L.append(Line(S, "Practitioner %d name" % i, full_name(p), required=True))
            L.append(Line(S, "Practitioner %d registration number" % i, p.get("reg_no"), required=True))
    else:
        L.append(Line(S, "Representative", "", note="leave blank - no power of attorney (pro se)"))
    S = "Domestic Benefit/National Stage Information"
    db = f.get("domestic_benefit") or []
    if ft == "nonprovisional_claiming_priority" and not db:
        L.append(Line(S, "Prior application", None, required=True,
                      note="benefit claims must be in the ADS (37 CFR 1.78(a)(3))"))
    for i, d in enumerate(db, start=1):
        L.append(Line(S, "Claim %d: Prior Application Status" % i, (d.get("status") or "pending").capitalize()))
        L.append(Line(S, "Claim %d: Application Number" % i, f.get("application_number") or "",
                      note="this application; blank when new"))
        L.append(Line(S, "Claim %d: Continuity Type" % i, d.get("relationship"), required=True))
        L.append(Line(S, "Claim %d: Prior Application Number" % i, d.get("prior_app_no"), required=True))
        L.append(Line(S, "Claim %d: Filing or 371(c) Date (YYYY-MM-DD)" % i, fmt_date(d.get("prior_filing_date")),
                      required=True))
        if (d.get("status") or "").lower() == "patented":
            L.append(Line(S, "Claim %d: Patent Number" % i, d.get("patent_number"), required=True))
            L.append(Line(S, "Claim %d: Issue Date" % i, fmt_date(d.get("issue_date")), required=True))
    if not db:
        L.append(Line(S, "Benefit claims", "", note="leave blank - no domestic benefit claimed"))
    S = "Foreign Priority Information"
    fp = f.get("foreign_priority") or []
    for i, p in enumerate(fp, start=1):
        L.append(Line(S, "Claim %d: Application Number" % i, p.get("app_no"), required=True))
        L.append(Line(S, "Claim %d: Country" % i, p.get("country"), required=True))
        L.append(Line(S, "Claim %d: Filing Date (YYYY-MM-DD)" % i, fmt_date(p.get("filing_date")), required=True))
        L.append(Line(S, "Claim %d: Access Code (if applicable)" % i, p.get("access_code") or ""))
    if not fp:
        L.append(Line(S, "Foreign priority", "", note="leave blank - none claimed"))
    S = "Statement under 37 CFR 1.55 or 1.78 for AIA Transition Applications"
    L.append(Line(S, "Claims priority to a pre-March 16, 2013 application and contains a post-March 16, 2013 claim",
                  False if not any((d.get("prior_filing_date") or "9999") < "2013-03-16" for d in db) else None,
                  kind="check"))
    S = "Authorization or Opt-Out of Authorization to Permit Access"
    L.append(Line(S, "A. DOES NOT authorize access by participating foreign IP offices (PDX opt-out)",
                  bool(f.get("pdx_opt_out")), kind="check", note="leave unchecked to allow priority document exchange"))
    L.append(Line(S, "B. DOES NOT authorize transmitting search results to the EPO",
                  bool(f.get("epo_search_opt_out")), kind="check"))
    S = "Applicant Information"
    apps = f.get("applicants") or []
    if not apps:
        L.append(Line(S, "Applicant", "", note="leave blank - the inventors are the applicant (37 CFR 1.45)"))
    kinds = {"assignee": "Assignee", "legal_representative": "Legal Representative under 35 U.S.C. 117",
             "joint_inventor": "Joint Inventor", "obligated_assignee": "Person to whom the inventor is obligated to assign",
             "proprietary_interest": "Person who shows sufficient proprietary interest"}
    for i, a in enumerate(apps, start=1):
        L.append(Line(S, "Applicant %d: type" % i, kinds.get(a.get("kind")), required=True))
        if a.get("org_name"):
            L.append(Line(S, "Applicant %d: Organization (check) and Organization Name" % i, a["org_name"]))
        else:
            L.append(Line(S, "Applicant %d: Given / Middle / Family Name" % i, full_name(a), required=True))
        _addr_lines(L, S, "Applicant %d" % i, a)
    S = "Assignee Information including Non-Applicant Assignee Information"
    asg = f.get("assignees") or []
    if not asg:
        L.append(Line(S, "Assignee", "", note="leave blank unless an assignee should print on the publication"))
    for i, a in enumerate(asg, start=1):
        L.append(Line(S, "Assignee %d: name" % i, full_name(a), required=True))
        _addr_lines(L, S, "Assignee %d" % i, a)
    S = "Signature (37 CFR 1.33(b))"
    signer = f.get("signer") or {}
    L.append(Line(S, "Signature", None, kind="signature"))
    L.append(Line(S, "Date (YYYY-MM-DD)", None, kind="date_sig"))
    L.append(Line(S, "First Name", signer.get("given"), required=True))
    L.append(Line(S, "Last Name", signer.get("family"), required=True))
    L.append(Line(S, "Registration Number", NOT_PRACTITIONER, kind="blank") if signer.get("reg_no") is None
             and pro_se(f) else Line(S, "Registration Number", signer.get("reg_no") or ""))
    L.append(Line(S, "Who signs", "a practitioner, or (pro se) every inventor-applicant unless a power of attorney "
                                  "exists; a juristic applicant needs a practitioner (Web ADS QSG; 1.33(b))",
                  kind="info"))
    return L


def _addr_lines(L, S, who, a):
    ad = a.get("address") or {}
    L.append(Line(S, "%s: Address 1" % who, ad.get("address1"), required=True))
    L.append(Line(S, "%s: Address 2" % who, ad.get("address2") or ""))
    L.append(Line(S, "%s: City" % who, ad.get("city"), required=True))
    L.append(Line(S, "%s: State/Province" % who, ad.get("state") or ""))
    L.append(Line(S, "%s: Country" % who, ad.get("country"), required=True))
    L.append(Line(S, "%s: Postal Code" % who, ad.get("postcode"), required=True))
    L.append(Line(S, "%s: Phone / Fax" % who, a.get("phone") or ""))
    L.append(Line(S, "%s: Email" % who, a.get("email") or ""))


WEB_ADS_ORDER = [
    # (Web ADS screen, ADS section prefixes) - Patent Center Web ADS QSG sections 3.1-3.13
    ("1. Application details (title, docket) and inventors", ("Header", "Secrecy", "Inventor Information")),
    ("2. Correspondence Information (QSG 3.2)", ("Correspondence Information",)),
    ("3. Application Information (QSG 3.3)", ("Application Information", "Filing By Reference")),
    ("4. Publication Information (QSG 3.4)", ("Publication Information",)),
    ("5. Representative Information (QSG 3.5)", ("Representative Information",)),
    ("6. Domestic Benefit/National Stage Information (QSG 3.6)", ("Domestic Benefit",)),
    ("7. Foreign Priority Information (QSG 3.7)", ("Foreign Priority", "Statement under 37 CFR 1.55")),
    ("8. Authorization or Opt-Out of Authorization to Permit Access (QSG 3.8)", ("Authorization",)),
    ("9. Applicant Information (QSG 3.9)", ("Applicant Information",)),
    ("10. Assignee Information (QSG 3.10)", ("Assignee Information",)),
    ("11. Summary, then Signature (QSG 3.12-3.13)", ("Signature",)),
]


# --------------------------------------------------------------------------- rendering

def render_worksheet(form: str, lines: List[Line], f: dict, title_extra: str = "",
                     pdf_status: Optional[str] = None) -> str:
    info = FORMS[form]
    out = ["# Worksheet: %s%s" % (info["title"], title_extra), ""]
    out.append("Generated %s by patentassist fill_forms.py from filing.json. Type each value exactly as shown. "
               "`[ask user]` means filing.json has no value yet: get it from the inventor or applicant, never guess." %
               datetime.date.today().isoformat())
    out.append("")
    if pdf_status:
        out.append("PDF: %s" % pdf_status)
        out.append("")
    open_req = [l for l in lines if l.required and l.kind in ("text", "check") and l.value is None]
    open_opt = [l for l in lines if not l.required and l.kind in ("text", "check") and l.value is None]
    out.append("Open items: %d required, %d optional." % (len(open_req), len(open_opt)))
    for l in open_req:
        out.append("- REQUIRED: %s - %s" % (l.section, l.label))
    out.append("")
    out.append("Signatures: this worksheet never fills a signature. Each signer types their own S-signature "
               "between slashes, for example `/Jane Q. Doe/`, with their name printed next to it "
               "(37 CFR 1.4(d)(2)). Do not edit certification statements printed on the form (37 CFR 1.4(d)(6)).")
    cur = None
    for l in lines:
        if l.section != cur:
            out += ["", "## %s" % l.section, "", "| Line | Enter | Note |", "|---|---|---|"]
            cur = l.section
        note = l.note + ("; PDF field `%s`" % l.field if l.field and l.kind not in ("info",) else "")
        out.append("| %s | %s | %s |" % (_md(l.label), _md(l.shown()), _md(note.strip("; "))))
    out.append("")
    return "\n".join(out)


def render_web_ads(lines: List[Line]) -> str:
    out = ["# Patent Center Web ADS entry worksheet", "",
           "Same data as the PTO/AIA/14 worksheet, grouped in the order of the Patent Center Web ADS Quick Start "
           "Guide (sections 3.1-3.13). Inventor screens are not in that guide's contents list; enter inventors "
           "where Patent Center asks for them. Rules from the guide: the Web ADS is for new utility and design "
           "submissions; do not also attach a PDF ADS; title and customer number or correspondence address are "
           "required; no special characters in the title; sessions time out after 30 minutes of inactivity.",
           "", "`[ask user]` = still missing. Signatures are never filled (37 CFR 1.4(d)(2)).", ""]
    used = set()
    for screen, prefixes in WEB_ADS_ORDER:
        sel = [l for l in lines if l.section.startswith(prefixes) and id(l) not in used]
        if not sel:
            continue
        out += ["## %s" % screen, "", "| Field | Enter | Note |", "|---|---|---|"]
        for l in sel:
            used.add(id(l))
            lab = l.label if l.section in ("Header",) else "%s: %s" % (l.section.split(" - ")[-1], l.label) \
                if " - " in l.section else l.label
            out.append("| %s | %s | %s |" % (_md(lab), _md(l.shown()), _md(l.note)))
        out.append("")
    rest = [l for l in lines if id(l) not in used]
    if rest:
        out += ["## Other", "", "| Field | Enter | Note |", "|---|---|---|"]
        for l in rest:
            out.append("| %s | %s | %s |" % (_md(l.label), _md(l.shown()), _md(l.note)))
    return "\n".join(out) + "\n"


def _md(s) -> str:
    return str(s if s is not None else "").replace("|", "\\|").replace("\n", " ")


# --------------------------------------------------------------------------- PDF inspection / filling

def pdf_kind(path: str) -> Tuple[str, dict]:
    """'acroform' | 'xfa' | 'hybrid' | 'none', plus details."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise UsageError("pypdf is not installed: pip install pypdf")
    r = PdfReader(path)
    root = r.trailer["/Root"]
    af = root.get("/AcroForm")
    af = af.get_object() if af is not None else None
    has_xfa = af is not None and "/XFA" in af
    widgets = 0
    for p in r.pages:
        for a in (p.get("/Annots") or []):
            if a.get_object().get("/Subtype") == "/Widget":
                widgets += 1
    det = {"pages": len(r.pages), "xfa": has_xfa, "needs_rendering": "/NeedsRendering" in root,
           "widgets": widgets, "fields": len(r.get_fields() or {})}
    if widgets == 0 or det["needs_rendering"]:
        return ("xfa" if has_xfa else "none"), det
    return ("hybrid" if has_xfa else "acroform"), det


def _widgets(reader) -> List[dict]:
    out = []
    for pi, p in enumerate(reader.pages):
        for a in (p.get("/Annots") or []):
            a = a.get_object()
            if a.get("/Subtype") != "/Widget":
                continue
            node, parts = a, []
            ft = tu = None
            while node is not None:
                if node.get("/T") is not None:
                    parts.append(str(node.get("/T")))
                ft = ft or node.get("/FT")
                tu = tu or node.get("/TU")
                par = node.get("/Parent")
                node = par.get_object() if par is not None else None
            name = ".".join(reversed(parts))
            ap = a.get("/AP")
            states = []
            if ap is not None and "/N" in ap:
                try:
                    states = [str(k) for k in ap["/N"].keys()]
                except AttributeError:
                    states = []
            rect = [float(v) for v in a.get("/Rect")]
            out.append({"page": pi, "name": name, "ft": str(ft) if ft else None, "tu": str(tu or ""),
                        "on": next((s for s in states if s != "/Off"), "/Yes"),
                        "y": (min(rect[1], rect[3]) + max(rect[1], rect[3])) / 2.0,
                        "x": min(rect[0], rect[2])})
    return out


def sb08_row_fields(widgets: List[dict]) -> Tuple[List[List[str]], List[List[str]]]:
    """Group SB/08a widgets into citation rows by tooltip and vertical position."""
    def cls(w):
        t = w["tu"].lower()
        if "unique citation" in t:
            return "cite"
        if "u.s. document number" in t:
            return "usdoc"
        if "foreign patent document" in t:
            return "fdoc"
        if "publication date" in t:
            return "date"
        if "name of patentee" in t:
            return "name"
        if "pages, columns" in t or "relevant passages" in t:
            return "pages"
        if "translation" in t:
            return "trans"
        return None
    ws = [dict(w, c=cls(w)) for w in widgets if w["page"] == 0]
    us_rows, f_rows = [], []
    for anchor in sorted([w for w in ws if w["c"] in ("usdoc", "fdoc")], key=lambda w: -w["y"]):
        near = [w for w in ws if abs(w["y"] - anchor["y"]) < 5.5 and w["c"]]
        near.sort(key=lambda w: w["x"])
        pick = {}
        for w in near:
            if w["c"] in ("usdoc", "fdoc") and w is not anchor:
                continue
            if w["c"] not in pick:
                pick[w["c"]] = w["name"]
        if anchor["c"] == "usdoc":
            us_rows.append([pick.get("cite"), anchor["name"], pick.get("date"), pick.get("name"), pick.get("pages")])
        else:
            f_rows.append([pick.get("cite"), anchor["name"], pick.get("date"), pick.get("name"), pick.get("pages"),
                           pick.get("trans")])
    return us_rows, f_rows


def fill_pdf(blank: str, out_path: str, values: Dict[str, Any], findings: List[dict], where: str) -> dict:
    """Fill AcroForm fields. values: field name -> str | bool. Signature fields are refused."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject, BooleanObject
    reader = PdfReader(blank)
    wid = _widgets(reader)
    by_name = {}
    for w in wid:
        by_name.setdefault(w["name"], w)
    text_vals, check_vals = {}, {}
    skipped = []
    for name, v in values.items():
        w = by_name.get(name)
        if w is None:
            skipped.append(name)
            continue
        if SIG_RE.search(name) or SIG_RE.search(w["tu"]) and w["tu"].strip().lower() in ("sign", "signature",
                                                                                         "enter your signature"):
            continue   # never fill a signature
        if w["ft"] == "/Btn":
            if v:
                check_vals[name] = w["on"]
        elif v not in (None, ""):
            text_vals[name] = str(v)
    if skipped:
        findings.append({"level": "WARN", "code": "field-missing", "where": where,
                         "message": "this PDF revision has no field(s) %s; enter them by hand from the worksheet"
                                    % ", ".join(sorted(skipped)[:8])})
    writer = PdfWriter()
    writer.append(reader)
    root_af = writer._root_object.get("/AcroForm")
    if root_af is not None:
        root_af = root_af.get_object()
        if "/XFA" in root_af:
            # hybrid form: drop the XFA layer so viewers show the AcroForm values we set
            del root_af["/XFA"]
        root_af[NameObject("/NeedAppearances")] = BooleanObject(True)
    for pi, page in enumerate(writer.pages):
        names_here = {w["name"] for w in wid if w["page"] == pi}
        tv = {k: v for k, v in text_vals.items() if k in names_here}
        cv = {k: v for k, v in check_vals.items() if k in names_here}
        if tv or cv:
            allv = dict(tv)
            allv.update(cv)
            try:
                writer.update_page_form_field_values(page, allv, auto_regenerate=False)
            except TypeError:
                writer.update_page_form_field_values(page, allv)
    with open(out_path, "wb") as fh:
        writer.write(fh)
    # verify persistence
    back = PdfReader(out_path).get_fields() or {}
    lost = []
    for k, v in list(text_vals.items()) + list(check_vals.items()):
        got = back.get(k, {}).get("/V") if k in back else None
        if got is None or str(got) != str(v):
            lost.append(k)
    sig_filled = [k for k, fv in back.items() if SIG_RE.search(k) and fv.get("/V") not in (None, "")]
    if sig_filled:
        findings.append({"level": "BLOCK", "code": "signature-filled", "where": where,
                         "message": "signature field(s) unexpectedly hold a value: %s" % ", ".join(sig_filled)})
    if lost:
        findings.append({"level": "BLOCK", "code": "values-not-persisted", "where": where,
                         "message": "values did not persist in %s: %s - use the worksheet"
                                    % (os.path.basename(out_path), ", ".join(lost[:8]))})
    return {"path": out_path, "text_fields": len(text_vals), "checkboxes": len(check_vals), "lost": lost}


def values_from_lines(lines: List[Line]) -> Dict[str, Any]:
    vals = {}
    for l in lines:
        if not l.field or l.kind in ("signature", "date_sig", "info", "blank"):
            continue
        if l.value is None:
            continue
        vals[l.field] = l.value
    return vals


# --------------------------------------------------------------------------- main operations

def canonical_form(name: str) -> str:
    k = re.sub(r"[\s_]", "", str(name)).upper()
    k = ALIASES.get(k, k)
    if k not in FORMS and k != "ALL":
        raise UsageError("unknown form %r (SB16, AIA14, AIA01, SB15A, SB15B, AIA82, SB08, all)" % name)
    return k


def load_filing(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            f = json.load(fh)
    except (OSError, ValueError) as ex:
        raise UsageError("cannot read filing file %s: %s" % (path, ex))
    sc = str(f.get("schema", ""))
    if not sc.startswith("patentassist/filing@") or sc.split("@")[-1].split(".")[0] != "1":
        raise UsageError("unsupported filing schema %r (want patentassist/filing@1)" % sc)
    return f


def build_lines(form: str, f: dict, ids: Optional[dict]):
    """Returns list of (suffix, lines, extra) - AIA01 yields one entry per inventor."""
    if form == "SB16":
        return [("", map_sb16(f), None)]
    if form == "AIA14":
        return [("", map_aia14(f), None)]
    if form == "AIA01":
        invs = f.get("inventors") or [{}]
        return [("-inventor%d" % i, map_aia01(f, inv, i), None) for i, inv in enumerate(invs, start=1)]
    if form in ("SB15A", "SB15B"):
        return [("", map_sb15(f, form), None)]
    if form == "AIA82":
        return [("", map_aia82(f), None)]
    if form == "SB08":
        lines, rows = map_sb08(f, ids)
        return [("", lines, rows)]
    raise UsageError("unknown form %s" % form)


def form_notes(form: str, f: dict, findings: List[dict]):
    ft = f.get("filing_type")
    ent = f.get("entity_status")
    if form == "SB16" and ft and ft != "provisional":
        findings.append({"level": "WARN", "code": "form-not-needed", "where": form,
                         "message": "SB/16 is the provisional cover sheet; filing_type is %s" % ft})
    if form == "SB08" and ft == "provisional":
        findings.append({"level": "BLOCK", "code": "ids-in-provisional", "where": form,
                         "message": "no IDS may be filed in a provisional (37 CFR 1.51(d))"})
    if form in ("SB15A", "SB15B") and ent and ent != "micro":
        findings.append({"level": "WARN", "code": "form-not-needed", "where": form,
                         "message": "entity_status is %s; micro entity certification not needed" % ent})
    if form == "SB15A" and f.get("micro_basis") == "higher_education":
        findings.append({"level": "WARN", "code": "wrong-micro-form", "where": form,
                         "message": "micro_basis is higher_education: use SB15B"})
    if form == "SB15B" and f.get("micro_basis") == "gross_income":
        findings.append({"level": "WARN", "code": "wrong-micro-form", "where": form,
                         "message": "micro_basis is gross_income: use SB15A"})
    if form == "AIA82" and not (f.get("representative") or {}).get("customer_no") and \
            not (f.get("representative") or {}).get("practitioners"):
        findings.append({"level": "WARN", "code": "form-not-needed", "where": form,
                         "message": "no representative in filing.json; a power of attorney is only for appointing "
                                    "registered practitioners"})


def profile_role(d: Optional[str], filing_path: str) -> Optional[str]:
    """state.json profile.role from the matter folder (or two levels above filing.json)."""
    for cand in ([os.path.join(d, "state.json")] if d else []) + \
            [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(filing_path))), "state.json")]:
        try:
            with open(cand, "r", encoding="utf-8") as fh:
                return ((json.load(fh).get("profile") or {}).get("role"))
        except (OSError, ValueError):
            continue
    return None


def operate(cmd: str, form_arg: str, filing_path: str, out_dir: str, pdf: Optional[str] = None,
            ids_path: Optional[str] = None, role: Optional[str] = None) -> dict:
    f = load_filing(filing_path)
    f = dict(f, _profile_role=role if role is not None else profile_role(None, filing_path))
    form = canonical_form(form_arg)
    findings = []
    if cmd == "fill" and form == "ALL":
        raise UsageError("fill takes one form at a time")
    if cmd == "fill" and not pdf:
        raise UsageError("fill needs --pdf path/to/blank.pdf")
    ids = None
    if ids_path is None:
        cand = os.path.join(os.path.dirname(os.path.abspath(filing_path)), "out", "ids.json")
        ids_path = cand if os.path.exists(cand) else None
    if ids_path and os.path.exists(ids_path):
        with open(ids_path, "r", encoding="utf-8") as fh:
            ids = json.load(fh)
    os.makedirs(out_dir, exist_ok=True)
    forms = list(FORMS) if form == "ALL" else [form]
    if form == "ALL":
        ft = f.get("filing_type")
        forms = [x for x in forms if not (x == "SB16" and ft and ft != "provisional")
                 and not (x == "SB08" and ft == "provisional")
                 and not (x in ("SB15A", "SB15B") and f.get("entity_status") not in (None, "micro"))
                 and not (x == "SB15A" and f.get("micro_basis") == "higher_education")
                 and not (x == "SB15B" and f.get("micro_basis") == "gross_income")
                 and not (x == "AIA82" and not (f.get("representative") or {}).get("customer_no")
                          and not (f.get("representative") or {}).get("practitioners"))]
    written, filled = [], []
    pdf_info = None
    kind = None
    if pdf:
        if not os.path.exists(pdf):
            raise UsageError("blank PDF not found: %s" % pdf)
        kind, pdf_info = pdf_kind(pdf)
    total_req = 0
    for fm in forms:
        form_notes(fm, f, findings)
        entries = build_lines(fm, f, ids)
        for suffix, lines, rows in entries:
            status = None
            if cmd == "fill":
                if kind in ("xfa", "none"):
                    status = ("%s is a dynamic XFA form (no AcroForm fields); it was NOT filled - type the values "
                              "below into it in Adobe Reader, or use the Patent Center Web ADS for the ADS"
                              % os.path.basename(pdf))
                else:
                    status = "%s is an AcroForm; a filled copy was written next to this worksheet" % os.path.basename(pdf)
            name = "%s%s-worksheet.md" % (fm.lower(), suffix)
            p = os.path.join(out_dir, name)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(render_worksheet(fm, lines, f, (" (%s)" % suffix.strip("-")) if suffix else "", status))
            written.append(p)
            req = [l for l in lines if l.required and l.kind in ("text", "check") and l.value is None]
            total_req += len(req)
            if fm == "AIA14":
                p2 = os.path.join(out_dir, "web-ads-worksheet.md")
                with open(p2, "w", encoding="utf-8") as fh:
                    fh.write(render_web_ads(lines))
                written.append(p2)
            if cmd == "fill" and kind in ("acroform", "hybrid"):
                vals = values_from_lines(lines)
                outs = []
                if fm == "SB08":
                    from pypdf import PdfReader
                    us_rows, f_rows = sb08_row_fields(_widgets(PdfReader(pdf)))
                    us, fo = rows["us"], rows["foreign"]
                    nus, nfo = max(len(us_rows), 1), max(len(f_rows), 1)
                    sheets = max(1, -(-len(us) // nus), -(-len(fo) // nfo))
                    for s in range(sheets):
                        v = dict(vals)
                        v["Text1"] = str(s + 1)
                        v["text2"] = str(sheets)
                        for i, r in enumerate(us[s * nus:(s + 1) * nus]):
                            for fname, val in zip(us_rows[i], r):
                                if fname and val not in (None, ""):
                                    v[fname] = val
                        for i, r in enumerate(fo[s * nfo:(s + 1) * nfo]):
                            for fname, val in zip(f_rows[i], r):
                                if fname and val not in (None, "", False):
                                    v[fname] = val
                        outs.append((os.path.join(out_dir, "sb08-filled%s.pdf" % ("-%d" % (s + 1) if sheets > 1 else "")), v))
                else:
                    outs.append((os.path.join(out_dir, "%s%s-filled.pdf" % (fm.lower(), suffix)), vals))
                for op, v in outs:
                    res = fill_pdf(pdf, op, v, findings, fm)
                    filled.append(res)
    if cmd == "fill" and kind in ("xfa", "none"):
        findings.append({"level": "INFO", "code": "xfa-not-filled", "where": os.path.basename(pdf),
                         "message": "dynamic XFA form: worksheet written, PDF not filled"})
    if total_req:
        findings.append({"level": "BLOCK", "code": "open-items", "where": "filing.json",
                         "message": "%d required value(s) missing - shown as [ask user] in the worksheet(s)" % total_req})
    blocking = sum(1 for x in findings if x["level"] == "BLOCK")
    return {"ok": blocking == 0, "worksheets": written, "filled": filled, "pdf": pdf_info, "pdf_kind": kind,
            "forms": forms, "findings": findings,
            "summary": {"blocking": blocking, "warnings": sum(1 for x in findings if x["level"] == "WARN"),
                        "open_required": total_req}}


def _resolve(path: Optional[str], d: str) -> Optional[str]:
    if path is None:
        return None
    if os.path.isabs(path) or os.path.exists(path):
        return path
    alt = os.path.join(d, path)
    return alt if os.path.exists(alt) else path


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _audit(d, rec, no_audit):
    if no_audit or not d or not os.path.isdir(d):
        return
    rec = dict(rec)
    rec["ts"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with open(os.path.join(d, "audit.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def run(args: dict) -> dict:
    """Tool entry point. args: {command: worksheet|fill, form, filing, out?, pdf?, ids?, dir?, no_audit?}"""
    d = args.get("dir", "patent")
    cmd = args.get("command")
    if cmd not in ("worksheet", "fill"):
        raise UsageError("command must be 'worksheet' or 'fill'")
    filing = _resolve(args.get("filing") or "draft/filing.json", d)
    out = args.get("out") or os.path.join(os.path.dirname(filing), "out")
    res = operate(cmd, args["form"], filing, out, _resolve(args.get("pdf"), d), _resolve(args.get("ids"), d),
                  role=profile_role(d, filing))
    for p in res["worksheets"] + [x["path"] for x in res["filled"]]:
        _audit(d, {"kind": "export", "path": p, "sha256": _sha256(p), "script": "fill_forms.py"},
               bool(args.get("no_audit")))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="USPTO form worksheets; fill AcroForm PDFs (never signatures)")
    sub = ap.add_subparsers(dest="command")
    for name in ("worksheet", "fill"):
        p = sub.add_parser(name)
        p.add_argument("form")
        p.add_argument("--filing", default="draft/filing.json")
        p.add_argument("--out", default=None)
        p.add_argument("--ids", default=None)
        if name == "fill":
            p.add_argument("--pdf", required=True)
        p.add_argument("--dir", default="patent")
        p.add_argument("--json", action="store_true")
        p.add_argument("--no-audit", action="store_true")
    a = ap.parse_args(argv)
    if not a.command:
        ap.print_help()
        return 2
    try:
        res = run({"command": a.command, "form": a.form, "filing": a.filing, "out": a.out,
                   "pdf": getattr(a, "pdf", None), "ids": a.ids, "dir": a.dir, "no_audit": a.no_audit})
    except UsageError as ex:
        print(json.dumps({"error": str(ex)}) if a.json else "error: %s" % ex,
              file=sys.stdout if a.json else sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=2, default=str))
    else:
        for x in res["findings"]:
            print("%s  %s  %s  %s" % (x["level"], x["code"], x["where"], x["message"]))
        for p in res["worksheets"]:
            print("worksheet: %s" % p)
        for x in res["filled"]:
            print("filled: %s (%d text, %d checkboxes%s)" % (x["path"], x["text_fields"], x["checkboxes"],
                                                            ", LOST %d" % len(x["lost"]) if x["lost"] else ""))
        if res["pdf_kind"]:
            print("pdf type: %s" % res["pdf_kind"])
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
