---
title: USPTO forms, Patent Center DOCX rules, and filing requirements (utility)
last_verified: 2026-11-18
sources:
  - https://www.uspto.gov/patents/apply/forms/forms-patent-applications-filed-or-after-september-16-2012 (form list and revision dates; page last updated Nov 10, 2026)
  - https://www.uspto.gov/patents/apply/forms/important-information-completing-application-data-sheet-ads (current ADS is aia0014pc.pdf "Updated March 2026"; Web ADS recommended; page updated Mar 19, 2026)
  - https://www.uspto.gov/sites/default/files/documents/ (form PDFs sb0016, sb0016pc, aia0014, aia0014pc, aia0001, aia0002, sb0015a, sb0015b, aia0082, sb0008a, sb0008b, sb0008c, sb0008pc, aia0096, sb0035 downloaded 2026-11-18 and checked with pypdf 6.9.2 for /AcroForm, /XFA and field counts)
  - https://www.uspto.gov/sites/default/files/documents/PATENTCENTER-Web-ADS-QSG.pdf (Web ADS: utility and design; pro se ADS must be signed by all inventors; "Request Not to Publish" option)
  - https://www.uspto.gov/patents/docx (DOCX rules, FAQ, surcharge, auxiliary PDF, feedback document; page last updated Aug 10, 2026)
  - https://www.uspto.gov/sites/default/files/documents/docx-supported-fonts.zip (supported font list, file "Master File-PROD-Fonts-March-2026")
  - https://www.uspto.gov/sites/default/files/documents/docx-feedback-warning-and-error-messages.zip (DOCX error and warning codes, August 2025 files)
  - https://www.uspto.gov/sites/default/files/documents/DOCX_Filing_Tips_and_Best_Practices_October_8_2024.pdf (headings, multi-section documents, preliminary amendments)
  - https://www.uspto.gov/sites/default/files/documents/DOCX_QSG_Final.pdf (DOCX intake for utility nonprovisional, utility provisional and 371; feedback document only pre-submission; June 2021)
  - https://www.uspto.gov/sites/default/files/documents/DOCXtoTIFFQRGAug2026.docx (from July 2026, DOCX is previewed as TIFF, not PDF)
  - https://www.uspto.gov/patents/apply/patent-center (identity verification required for all users from Sept 11, 2025; design DOCX Feb 2026; page updated Nov 6, 2026)
  - https://www.uspto.gov/patents/apply/applying-online/getting-started-new-users (USPTO.gov account, ID.me or notarized paper form PTO-2042a, self-enrollment)
  - https://www.federalregister.gov/d/2025-17543 (90 FR 44050, Sept 11, 2025: updated legal framework; registration required; DOCX validated)
  - https://www.ecfr.gov/current/title-37/chapter-I/subchapter-A/part-1 (37 CFR 1.4, 1.6, 1.31, 1.33, 1.46, 1.51, 1.52, 1.53, 1.55, 1.56, 1.63, 1.64, 1.72, 1.75, 1.77, 1.78, 1.84, 1.97, 1.98, 1.211, 1.213; eCFR current as of 2026-11-16)
  - https://www.ecfr.gov/current/title-37/chapter-I/subchapter-A/part-3/section-3.73 (statement under 3.73(c))
  - https://www.uspto.gov/web/offices/pac/mpep/index.html (MPEP 9th ed., Rev. 01.2024 — the current revision: sections 140, 211, 505, 601, 607)
  - https://www.govinfo.gov/content/pkg/USCODE-2023-title35/html/USCODE-2023-title35.htm (35 U.S.C. 119(e), 122(b), 184)
---

# Forms, Patent Center DOCX, and filing requirements

## 1. Forms

The check was run on 2026-11-18. "Fields" counts the AcroForm fields that pypdf reported (text fields / buttons). For XFA forms the number is the count of `<field>` elements in the XFA template. That count is approximate, because it can include repeated subforms.

| Form | Purpose | Provisional | Nonprovisional | Current revision | PDF type | Fields |
|---|---|---|---|---|---|---|
| **PTO/SB/16** (sb0016.pdf) | Provisional application cover sheet | Required cover sheet, unless an ADS or a cover letter is used (1.51(c)(1), 1.53(c)(1)) | No | **01-25** | AcroForm, no XFA | 58 (43 text, 15 buttons), 3 pages |
| SB/16 Patent Center "auto-load" (sb0016pc.pdf) | Same; Patent Center reads its data. USPTO marks it "RECOMMENDED" | Same as above | No | **03-26** | **Dynamic XFA** (NeedsRendering, 0 AcroForm fields) | about 47 XFA fields |
| **PTO/AIA/14** ADS, current (aia0014pc.pdf) | Application data sheet (1.76): inventors, applicant, correspondence, benefit and priority claims, publication requests | Optional; can serve as the cover sheet | Needed for: benefit claims (must be in the ADS, 1.78(a)(3)); foreign priority claims (1.55(d)); naming an assignee as applicant (1.46(b)); postponing the declaration (1.53(f)(3)) | **03-26** ("Updated March 2026") | **Dynamic XFA** | about 197 XFA fields |
| PTO/AIA/14, old file (aia0014.pdf) | Same, older revision. The forms index page still says 01/2022 | | | 01-22 | Dynamic XFA | about 197 |
| **Patent Center Web ADS** | Web form that replaces the ADS PDF. Patent Center makes the PDF itself | Patent Center QSG says "Utility and Designs". Use for provisionals *(unconfirmed)* | USPTO recommends it for new utility and design applications. Not allowed in follow-on submissions | QSG dated March 2024 | n/a | n/a |
| **PTO/AIA/01** | Inventor's declaration (1.63) used with an ADS. One per inventor | No | Yes. May be postponed until the issue fee is paid if the ADS names each inventor's legal name, mailing address and residence (1.53(f)(3)) | **06-12** | AcroForm | 8 (6 text, 2 buttons), 2 pages |
| **PTO/AIA/02** | Substitute statement (1.64) in place of a declaration. Used when the inventor is dead, legally incapacitated, refuses to sign, or cannot be found after diligent effort. Signed by an applicant under 1.43, 1.45 or 1.46 | No | Only when needed | **06-15** | AcroForm | 38 (25 text, 13 buttons), 3 pages |
| **PTO/SB/15A** | Micro entity certification, gross income basis | If paying micro fees | If paying micro fees | **11-26** | AcroForm | 10 (9 text, 1 button), 2 pages |
| **PTO/SB/15B** | Micro entity certification, higher-education basis | If paying micro fees | If paying micro fees | **11-26** | AcroForm | 16 (14 text, 2 buttons), 2 pages |
| **PTO/AIA/82** (82A transmittal + 82B power of attorney, one PDF) | Applicant appoints registered practitioners | Optional | Optional. A juristic applicant, or (from July 20, 2026) any applicant domiciled outside the US, must act through a practitioner (1.31(a), 1.33(b)) | **07-13** | AcroForm | 63 (52 text, 11 buttons), 4 pages |
| **PTO/SB/08** Patent Center auto-load (sb0008pc.pdf) | IDS form. It includes the IDS size-fee assertion. USPTO marks it "RECOMMENDED" | **Not allowed.** No IDS may be filed in a provisional (1.51(d)) | Yes, within the 1.97 windows | **03-26** | **Dynamic XFA** | about 74 XFA fields |
| PTO/SB/08a and SB/08b (pages 1 and 2) | IDS forms, older layout with **no** size-fee assertion | No | Yes; add the SB/08c assertion | Forms page: **06/2015**. Printed footer: "(07-09)" | AcroForm | 08a: 139 (133 text, 6 buttons); 08b: 38 (28 text, 10 buttons) |
| PTO/SB/08c | Stand-alone IDS size-fee written assertion (1.98(a)(4)) | No | With an SB/08a or 08b IDS | **01-25** | AcroForm | 18 (13 text, 5 buttons), 4 pages |
| **PTO/AIA/96** | Statement under 37 CFR 3.73(c): an assignee that is not the original applicant proves ownership so it can act (for example, to sign a power of attorney) | Rarely | When an assignee takes action | **11-23** | AcroForm | 49 (39 text, 10 buttons), 3 pages |
| **PTO/SB/35** | Nonpublication request (35 U.S.C. 122(b)(2)(B)(i); 1.213). The ADS "Request Not to Publish" box does the same job | No (provisionals are never published) | Only **on filing** | **07-09** | AcroForm | 8 (all text), 2 pages |

What this means for `fill_forms.py`:

- **AcroForms can be filled with pypdf:** SB/16 (01-25), AIA/01, AIA/02, SB/15A, SB/15B, AIA/82, SB/08a, 08b and 08c, AIA/96, SB/35.
- **Dynamic XFA forms** (NeedsRendering true, no AcroForm widgets) cannot be filled reliably with pypdf: the current ADS (AIA/14, 03-26) and the auto-load SB/16 and SB/08. The ADS info page warns the file "may not be viewable in your browser" and says to open it in Adobe Reader.
  - **For the ADS,** use the **Patent Center Web ADS** plus a field-by-field worksheet.
  - **For a provisional,** fill the AcroForm SB/16 (01-25).
  - **For an IDS,** fill SB/08a or 08b and add SB/08c, or use the auto-load SB/08 in Adobe.
- The forms index page says expiration dates printed on forms come from the Paperwork Reduction Act. An expired date does **not** make a form invalid. The AIA/01 PDF's "Approved for use through" text is garbled in the PDF itself and could not be read.
- **Do not edit certification statements on USPTO forms** (1.4(d)(6)).
- **Never sign for the user.** See signatures in section 4.

## 2. Patent Center DOCX rules

### What must be DOCX

- **Utility nonprovisional** applications filed under 35 U.S.C. 111(a) on or after **Jan 17, 2024** pay the **non-DOCX surcharge** if the specification, claims or abstract is not DOCX (1.16(u): $430 / $172 / $86). This includes continuations, divisionals and CIPs.
- **Not covered by the surcharge:** design, plant and provisional applications (1.16(u)).
- **Same-day preliminary amendment.** It is part of the original disclosure (1.115(a)). It must be DOCX to avoid the surcharge. Use the "Is a Preliminary Amendment in DOCX format being filed" option or file it as a follow-on. A preliminary amendment filed **after** the filing date does not trigger the surcharge (DOCX FAQ).
- **Drawings** may be DOCX **or PDF**, with **no surcharge for PDF** drawings (DOCX FAQ).
- **Where DOCX works.** DOCX intake works for utility nonprovisional, **utility provisional** and 371 national stage filings (DOCX QSG). Design applications were added in **February 2026** (Patent Center page).
- **Auxiliary PDF.** You may also upload one backup "auxiliary" PDF with the DOCX, at no fee. The option is "extended until further notice", Patent Center only. Upload the DOCX first. Use the dedicated auxiliary-PDF slot, not the normal upload area (DOCX page; Best Practices).

### Required formatting (37 CFR 1.52 and Patent Center checks)

| Item | Rule | Source |
|---|---|---|
| Page size | US Letter 21.6 x 27.9 cm (8.5 x 11 in) or A4 21.0 x 29.7 cm. DOCX **error** if larger than Letter or A4 | 1.52(a)(1)(ii); error 2006 |
| Orientation | Portrait. DOCX **error** if not portrait | 1.52(a)(1)(iii); error 2008 |
| Margins | Top **2.0 cm**, left **2.5 cm**, right **2.0 cm**, bottom **2.0 cm**, at least. DOCX **warning** if not met | 1.52(a)(1)(ii); warning 3013 |
| Line spacing | **1.5 or double** (spec, claims, abstract). Warnings for bad spacing and "At least" spacing | 1.52(b)(2)(i); warnings 3052, 3083 |
| Font | Non-script font, **12 pt preferred**. Capital letters ideally at least 0.3175 cm (0.125 in) tall, never under 0.21 cm (0.08 in, about 6 pt). The font **must be on the USPTO supported list** or the upload **errors** | 1.52(b)(2)(ii); error 2009 |
| Columns | One column only | 1.52(b)(2)(iii); warning 3054 |
| Claims | Start on a **new page**. No other material on claim pages. Separate each element or step by a line indentation | 1.52(b)(3), 1.75(h), 1.75(i) |
| Abstract | Starts on a **new page**, after the claims, headed "Abstract" or "Abstract of the Disclosure". Preferably **150 words or fewer**. DOCX warns over 150 words, under 50 words, more than one paragraph, or legal words like "means" and "said" | 1.72(b); warnings 3008, 3062, 3020, 3063 |
| Page numbers | Number pages consecutively from 1, centered, preferably at the bottom. DOCX adds numbers if missing | 1.52(b)(5); warning 3027 |
| Paragraph numbers | Optional by rule ("may"). If used: at least 4 digits in square brackets, bold, e.g. **[0001]**, then a gap of about 4 spaces. Do not number headings, claims, abstract, tables or lists. DOCX warns if numbering is missing, duplicated, not 4 digits or not consecutive | 1.52(b)(6); warnings 3007, 3028, 3041-3043 |
| Section headings | Uppercase, not underlined, not bold. Use the USPTO-recognized headings so Patent Center can split the document. Claims, abstract and drawings headings must be the **first line** of their section | 1.77(c); Best Practices; heading list zip (May 2025) |
| Title | 500 characters or fewer | 1.72(a) |

### Supported fonts

From the USPTO list "Master File-PROD-Fonts-March-2026", 53 entries:

aptos, aptos black, aptos display, aptos extra, aptos light, aptos mono, aptos narrow, aptos semi, arial, arial black, arial narrow, arial rounded mt, arial unicode ms, batang, batangche, bierstadt, bierstadt display, calibri, calibri light, cambria, cambria math, castellar, century, century gothic, century schoolbook, courier new, dengxian, georgia, helvetica, liberation, liberation sans, lucida sans, ms mincho, ms pmincho, mingliu extb, monaco, new gulim, pmingliu, pmingliu extb, segoe ui symbol, simsun, stixgeneral, symbol, tahoma, times, times new roman, times-new-roman, timesnewromanpsmt, trebuchet ms, verdana, wide latin, biz udgothic, hysinmyeongjo-medium.

**Safe default for the skill:** Times New Roman 12 pt or Arial 12 pt, with Cambria Math for equations. Check equation and symbol fonts too: error 2039 means a character cannot be shown in its font.

### What DOCX validation checks

**Errors (marked X): you must fix them before you can submit.** From the August 2025 list:

- corrupt or not a real DOCX (1004, 1006)
- no recognized section headings (2000)
- content controls (2002), custom XML (2003)
- page larger than Letter or A4 (2006), landscape (2008)
- unsupported font (2009), character not in its font (2039)
- more than one abstract (2012)
- forbidden field codes: document automation, form checkbox and dropdown, RD, user information, mail merge, bookmark references, INCLUDEPICTURE and INCLUDETEXT (graphics must be embedded), PAGEREF, STYLEREF, QUOTE, AUTONUM (2015-2030)
- custom-dash charts (2042)
- unsupported image type (2051). Allowed types: **EMF, WMF, JPEG, TIFF, BMP, GIF, PNG**
- old Equation 3 objects (2071)

**Warnings (marked with a triangle): you may still submit.**

- *Claims:* non-numeric claim numbers, a claim that refers to a missing or later claim or to itself, improper multiple-dependent chains, a claim not ending in a period, a claim not starting with a capital letter, or more than one sentence in a claim (3009, 3015, 3021-3026, 3029, 3032-3038, 3040).
- *Paragraphs and margins:* paragraph-numbering problems; bad margins.
- *Images:* color or grayscale images (3014), SVG images (2050), figures inside the specification (3050), no figures in the drawings section (3053).
- *Other:* tracked changes, OLE objects, watermarks, non-white background, non-English text, line spacing, text-wrapped images.

**Automatic fixes (4000 series). Patent Center will do these silently:**

- accept tracked changes
- delete comments, bookmarks, hidden text and text decorations
- turn hyperlinks into plain text
- freeze dynamic dates and formula fields
- replace SmartArt, charts and drawing objects with images
- remove line numbering and tables of authorities

Also:

- **Metadata** (author, company and so on) is stripped automatically (DOCX FAQ).
- **Macro-enabled files (DOCM) are rejected** (DOCX FAQ).

**So `build_docx.py` should produce:**

- plain styles
- no fields, content controls, comments, tracked changes or bookmarks
- embedded PNG or TIFF images only
- one column, portrait Letter
- the margins and spacing above
- USPTO headings

### The feedback document

- Patent Center makes a **feedback document** after you upload a DOCX and **before you submit**. It summarizes and pinpoints each warning and error (DOCX FAQ; Best Practices).
- It is **only available before submission.** It is not saved in Patent Center or any USPTO system afterwards (DOCX QSG). **Download it and keep it** in the filing folder.
- **Review the split files before submitting** (spec, claims, abstract, drawings). Patent Center now lets you view split files pre-submission (Feb 2026).
- **Since July 2026,** the pre-submission preview is a **TIFF rendering**, not a PDF. After submission the documents can be downloaded as DOCX, PDF or XML (DOCX to TIFF QRG, Aug 2026).
- **The USPTO's validated DOCX rendering is the official record** (FR notice June 2, 2021, linked on the DOCX page).
  - If the rendering differs from what you meant, petition under **1.181** if the validated DOCX supports the correction.
  - Petition under **1.182** if only the auxiliary PDF supports it. The 1.17(f) fee for that petition is waived (DOCX FAQ).
- **One file or several.** One multi-section DOCX (spec, claims, abstract, drawings) is allowed for utility nonprovisional initial filings. Patent Center labels it "Application body structured text". Do not override that label (Best Practices).

### Account and identity verification for a pro se filer

- **Since Sept 11, 2025, identity verification is required for all Patent Center users.** Guest and unregistered filing ended (Patent Center page; 90 FR 44050).
- **Step 1. Create a USPTO.gov account** and set up multi-factor authentication. Email is no longer accepted as an authentication method (Patent Center page).
- **Step 2. Verify identity.** Pick one route:
  - **ID.me online** takes about 30 minutes. You need a government photo ID with a name **exactly** matching the USPTO.gov account, your Social Security number, a camera-equipped device, and consent to a credit-header check (no credit impact). You can use self-service with a selfie, or a video call with an agent.
  - **Paper form PTO-2042a** ("Patent Electronic Verification" form). It must be **notarized**. Mail the original to Mail Stop EBC Customer Number, Commissioner for Patents, P.O. Box 1450, Alexandria, VA 22313-1450. Processing takes about 1-2 weeks (the page also says "up to 10 business days"). You can add a Customer Number request (SB/125).
- **Step 3. Self-enroll in Patent Center** as "Independent Inventor". Link an existing customer number, or create one after enrolling. The self-enrollment bug for inventors without a customer number was marked resolved on Jan 29, 2026.
- **Help:** Patent EBC, 866-217-9197, ebc@uspto.gov.
- **Practice first.** Patent Center has a **training mode** for test DOCX submissions (DOCX page).
- **Foreign-domiciled applicants** (any applicant domiciled outside the US) must use a registered practitioner from **July 20, 2026** (1.31(a)(2); 91 FR 13510).

## 3. Filing requirements

### What gets a filing date (37 CFR 1.53)

| | Provisional (1.53(c)) | Utility nonprovisional (1.53(b)) |
|---|---|---|
| Minimum for a filing date | A specification, with or without claims | A specification, with or without claims |
| Also needed (can come later with a surcharge) | Cover sheet (SB/16, ADS or cover letter) and filing fee. Late: 1.16(g) surcharge. Without a cover sheet the filing "will be treated as" a nonprovisional (1.53(c)(1)). In Patent Center, choose the provisional submission type | Claims, filing + search + exam fees, inventor's oath or declaration. Late: 1.16(f) surcharge |
| Drawings | "When necessary" (1.51(c)(3)) | "When necessary" (1.51(b)(3)) |
| New matter after filing | Not allowed | Not allowed (1.53(b)) |
| E-filing receipt date | The **Eastern Time** date the USPTO receives it, **even on a weekend or holiday** (1.6(a)(4)) | Same |

Design applications are different. They need at least one claim and the drawings to get a filing date (1.53(b)).

**Missing parts.** If items are missing, the USPTO sends a notice. The period is "usually two months" (MPEP 601.01(a)). It can be extended under 1.136(a) unless the notice says otherwise (1.136(a)(1) rule text). If no correspondence address was given, the deadline is 3 months from filing for a nonprovisional (1.53(f)(2)), or 2 months for a provisional (1.53(g)(2)).

### Postponing the declaration (1.53(f)(3))

- **Conditions.** The application must be original (not a reissue). It must have an ADS giving each inventor's **legal name** and **mailing address**, plus residence if different.
- **Deadline.** Each declaration (AIA/01) or substitute statement (AIA/02) is due **no later than the date the issue fee is paid**. This deadline cannot be extended (1.136(c)).
- **Surcharge.** The 1.16(f) surcharge ($170 / $68 / $34) is still due within the missing-parts period if a declaration for every inventor is not filed on the filing date (MPEP 601.01(a)). Filing all declarations at filing avoids it.

### Provisional to nonprovisional (12 months) and restoration

- **12-month deadline.** File the nonprovisional (or PCT) **no later than 12 months** after the provisional filing date (35 U.S.C. 119(e)(1); 1.78(a)(1)). If day 12 months falls on a Saturday, Sunday or federal holiday, the deadline moves to the next business day (119(e)(3); 1.7(b)).
- **Common inventor and fee.** The provisional must name at least one inventor of the later application. Its basic filing fee must have been paid (1.78(a)(2)).
- **Benefit claim in the ADS.** The benefit claim must be in the **ADS** (1.78(a)(3)). It is due within the later of **4 months from the nonprovisional filing or 16 months from the provisional filing** (1.78(a)(4)). A late claim needs a petition under 1.78(c) and the 1.17(m) fee.
- **Restoration.** If the nonprovisional is filed **within 2 months after** the 12-month deadline, benefit can be restored by petition in the nonprovisional (1.78(b)). The petition needs the ADS reference, the 1.17(m)(3) fee ($2,260 / $904 / $452), and a statement that the delay was unintentional. **Do not plan on it.**
- **Converting instead.** Converting a provisional to a nonprovisional (1.53(c)(3)) is allowed but measures patent term from the provisional date. The rule itself recommends claiming benefit instead.
- **Foreign priority** (Paris) is the same idea: 12 months (6 for designs), 2-month restoration (1.55(b), (c)). The claim goes in the ADS (1.55(d)).

### Foreign filing license

- **The filing counts as a petition for a license.** Filing a US application is treated as a petition for a foreign filing license (37 CFR 5.12(a)). **The filing receipt shows whether a license was granted** and from what date (MPEP 140).
- **Without a license,** you may not file abroad (including a PCT filed abroad) until **6 months** after the US filing. After that it is allowed if no secrecy order was imposed (35 U.S.C. 184(a); MPEP 140).
- **Check every filing receipt** for the "Foreign Filing License Granted" line.

### Publication at 18 months and nonpublication requests

- **Publication.** Utility nonprovisional and 371 applications are published promptly after **18 months from the earliest claimed filing date** (1.211(a)). Provisionals, designs and reissues are never published (1.211(b)). The publication fee is **$0** (1.18(d)(1)).
- **Nonpublication request (1.213(a)).** Use SB/35 or the ADS "Request Not to Publish" box. It must be filed **with the application on filing**. It must certify that the invention **has not been and will not be** the subject of a foreign or PCT application that publishes at 18 months. A 1.33(b) party must sign it.
- **Rescinding.** It can be rescinded at any time (1.213(b)).
- **Later foreign filing.** If you later file abroad or under the PCT, you **must notify the USPTO within 45 days**. Missing that notice abandons the US application (1.213(c); 35 U.S.C. 122(b)(2)(B)(iii)).
- **Advice for the skill:** request nonpublication only if the user will **never** file abroad.

### Duty of disclosure and IDS (1.56, 1.97, 1.98)

- **Who has the duty.** Each inventor, each attorney or agent, and anyone else substantively involved has a duty of candor. That includes disclosing known information that is **material to patentability** (1.56(a), (c)).
- **How long.** The duty lasts for each pending claim until it is cancelled or withdrawn, or the application is abandoned.
- **Penalty.** Fraud, or a bad-faith or intentional breach, means no patent will be granted (1.56(a)).
- **Provisionals.** No IDS may be filed in a provisional (1.51(d)).

| Window | Rule | Needs |
|---|---|---|
| Within 3 months of the filing date, **or** before the first Office action on the merits, **or** before the first action after an RCE | 1.97(b) | No statement and no fee (only any size fee) |
| After that, but before a final action, notice of allowance, or other action closing prosecution | 1.97(c) | 1.97(e) statement **or** the 1.17(p) fee ($280 / $112 / $56) |
| After that, on or before paying the issue fee | 1.97(d) | 1.97(e) statement **and** the 1.17(p) fee |
| After the issue fee is paid | — | Not considered under 1.97. The USPTO forms page lists a QPIDS certification form for this stage |

- **The 1.97(e) statement** says one of two things:
  - every item was first cited by a foreign office in a counterpart application no more than 3 months before the IDS; or
  - no item was cited by a foreign office, and no listed person knew of any item more than 3 months before the IDS (after reasonable inquiry).
- **No extensions of time** apply to IDS windows (1.97(f)).
- **Every IDS** must include the **size-fee assertion** (1.98(a)(4)). Size fees apply over 50, 100 and 200 cumulative items. See fees.md.
- **A non-compliant IDS** is placed in the file but not considered (1.97(i)).

### Drawings (37 CFR 1.84)

| Item | Rule |
|---|---|
| Sheet size | A4 (21.0 x 29.7 cm) or Letter (21.6 x 27.9 cm). All sheets the same size (1.84(f)) |
| Margins | Top **2.5 cm**, left **2.5 cm**, right **1.5 cm**, bottom **1.0 cm**, at least. No frames around the usable area. Usable area at most **17.6 x 24.4 cm on Letter**, 17.0 x 26.2 cm on A4 (1.84(g)) |
| Lines | Black, dense, uniformly thick, durable. Must survive reduction to two-thirds size. No "actual size" or scale notes (1.84(k), (l)) |
| Reference numerals and letters | At least **0.32 cm (1/8 in)** tall. Not encircled, bracketed or in quotes. Oriented the same way as the view. Not placed on hatching (1.84(p)) |
| Views | As many as needed: plan, elevation, section, perspective, detail. Grouped and separated. No projection lines or center lines. Never on spec, claim or abstract sheets (1.84(h)). Section planes shown by broken lines with numbered ends and arrows. Hatching about 45 degrees |
| View numbers | "FIG. 1", "FIG. 2"... consecutively. Partial views use 1A, 1B. **A single view is not numbered and has no "FIG."** (1.84(u)) |
| Sheet numbers | "1/3", "2/3"... centered at the top inside the usable area, larger than the reference numerals (1.84(t)) |
| Color | Utility color drawings need a **granted petition** under 1.84(a)(2). It needs the 1.17(h) fee ($150 / $60 / $30), 1 set of color drawings if e-filed, and a set paragraph added to the brief description of drawings. Not allowed in PCT applications |
| Photographs | Only if they are the only practicable medium (gels, micrographs, cell cultures and similar). The examiner may require a drawing instead (1.84(b)) |
| DOCX notes | Color or grayscale images trigger warning 3014. Drawings may be uploaded as PDF with no surcharge |

### Title, abstract and section order

- **Title:** 500 characters or fewer, as short and specific as possible (1.72(a)).
- **Abstract:** on its own sheet. It may be "as concise as the disclosure permits, preferably not exceeding 150 words" (1.72(b)).
- **Specification order** (1.77(b)), each with an uppercase heading (1.77(c)):
  1. Title
  2. Cross-reference to related applications
  3. Statement on federally sponsored research
  4. Names of parties to a joint research agreement
  5. Incorporation by reference of sequence, program or table files
  6. Statement on prior disclosures by the inventor
  7. Background
  8. Brief summary
  9. Brief description of the drawings
  10. Detailed description
  11. Claims
  12. Abstract
  13. Sequence listing (PDF/paper)
- **Whole application order** (1.77(a)): transmittal, fee transmittal, ADS, specification, drawings, declaration.

### Signatures (37 CFR 1.4(d), 1.33(b))

- **S-signature** (1.4(d)(2)):
  - It is typed between slashes, e.g. `/Jane Q. Inventor/`.
  - It may contain letters, numbers, spaces, commas, periods, apostrophes and hyphens.
  - **The signer must type it personally.**
  - The signer's name must be printed or typed next to it.
  - Practitioners add their registration number.
- **Other allowed signatures:** a graphic image of a handwritten signature or of an S-signature (1.4(d)(3)), or another electronic signature "of a form specified by the Director" (1.4(d)(4)). Which electronic signature tools qualify is not listed here *(unconfirmed)*.
- **Submitting someone else's signature.** Whoever submits a document signed by another person must have a reasonable basis to believe that person really signed it. They should keep evidence (1.4(d)(5)(ii)).
- **Who signs** (1.33(b)): a practitioner of record, a practitioner acting in a representative capacity, or the applicant.
  - A pro se ADS must be signed by **all** inventor-applicants unless a power of attorney exists (Web ADS QSG).
  - Papers for a juristic entity, or (from July 20, 2026) for any foreign-domiciled applicant, must be signed by a practitioner.
- **Ownership papers.** An assignee that files as applicant (1.46) should record its ownership papers by the time the issue fee is paid (1.46(b)(1)). An assignee that is not the original applicant files a 3.73(c) statement (AIA/96) before it can act.
- **The skill never signs.** It leaves each signature line for the signer.

## 4. Patent Center document descriptions

`last_verified: 2026-11-18`. Each file uploaded in Patent Center gets a **document description**, which sets how the USPTO indexes it in the image file wrapper. The strings below are copied from the sources listed under the table. Before uploading, confirm each one in the upload screen's "Help with document description" link: the USPTO calls that the complete current list.

| Document | Provisional | Nonprovisional (111(a)) | Doc code | Source |
|---|---|---|---|---|
| Specification | Specification | Specification | SPEC | A |
| Claims | Claims | Claims | CLM | A |
| Abstract | Abstract | Abstract | ABST | A |
| One DOCX holding the spec, claims and abstract | Specification (see note 2) | Application body structured text document. Patent Center splits it into Specification, Claims, Abstract | not listed | C (screenshot text), E, F |
| Drawings (black and white line art) | Drawings-only black and white line drawings | Drawings-only black and white line drawings | DRW | A |
| Drawings with color or photographs | not listed | Drawings-other than black and white line drawings | DRW.NONBW | A |
| PTO/SB/16 cover sheet | Provisional Cover Sheet (SB16) | n/a | TR.PROV | A |
| PTO/AIA/14 ADS (PDF; the Web ADS needs no upload) | Application Data Sheet | Application Data Sheet | ADS | A |
| PTO/AIA/01 declaration | n/a (a provisional needs none) | Oath or Declaration filed | OATH | A |
| PTO/SB/15A micro entity, gross income | not listed (see note 1) | Certification of Micro Entity (Gross Income Basis) | MES.GIB | A, B |
| PTO/SB/15B micro entity, higher education | not listed (see note 1) | Certification of Micro Entity (Education Basis) | MES.IHEB | A, B |
| PTO/AIA/82 power of attorney | Power of Attorney | Power of Attorney | PA.. | A, B |
| PTO/SB/08 IDS | not allowed (37 CFR 1.51(d)) | Information Disclosure Statement (IDS) Form (SB08) | IDS | A |
| PTO/SB/06 fee worksheet | Fee Worksheet (SB06) | Fee Worksheet (SB06) | WFEE | A, B |
| PTO/AIA/15 new-application transmittal | Transmittal of New Application | Transmittal of New Application | TRNA | A |
| Auxiliary PDF of a DOCX filing | n/a | Auxiliary PDF of Application | Aux.PDF | C, D |

Notes:
1. **Micro entity certification in a provisional.** List A gives no provisional filing type for MES.GIB or MES.IHEB, and no source checked says what Patent Center offers today. Pick the description the upload screen offers for the certification, or attach the SB/15A or SB/15B under the closest description and confirm it before submitting.
2. **One DOCX in a provisional.** The DOCX page says multi-section DOCX processing is for utility nonprovisional initial filings. For a provisional, upload the DOCX as "Specification", or split it with `build_docx.py --split` and upload Specification, Claims and Abstract separately. Patent Center indexes PDF files named Spec, Specification, Claims, Abstract, Drawing or Drw under that description automatically (F, Q11).
3. **Splitting a combined DOCX.** Detection uses the section headings (SPECIFICATION, "What is claimed is", ABSTRACT; E, appendix 4.1). For a single-section DOCX, the description can be changed with "Edit document description" (E).
4. **Fee worksheet.** List A says USPTO staff use the SB/06 to work out fees, so a filer rarely uploads it. `fees.md` is a working file and is not uploaded.
5. **Currency.** List A is dated 2022, so newer DOCX-era descriptions (the structured text document) come from Patent Center guides, not from the list.

Sources:
- A. Document Description List (XLS), file header "Updated 04/27/2022": https://www.uspto.gov/sites/default/files/documents/Document_Descriptions_List.xls. Landing page (last updated Nov 28, 2023): https://www.uspto.gov/patents/apply/filing-online/efs-info-document-description
- B. Form headers: https://www.uspto.gov/sites/default/files/documents/sb0015a.pdf (11-26), sb0015b.pdf (11-26), aia0082.pdf (07-13), sb0006.pdf (01-25)
- C. Patent Center Track One QSG, September 2024 (upload-screen screenshots, read by OCR): https://www.uspto.gov/sites/default/files/documents/pc-qsg-trackone.pdf
- D. Auxiliary PDF QRG, October 2023: https://www.uspto.gov/sites/default/files/documents/AUX_PDF_2023.pdf
- E. DOCX page (last updated Aug 10, 2026): https://www.uspto.gov/patents/docx ; DOCX QSG, June 2021: https://www.uspto.gov/sites/default/files/documents/DOCX_QSG_Final.pdf
- F. Top 25 Patent Center Questions (Sept 2025): https://www.uspto.gov/sites/default/files/documents/Top_25_Patent_Center_Questions.pdf

`scripts/manifest.py` reads the block below (the same strings as the table) to write `draft/out/manifest.md` and `manifest.json`. Update the table and the block together. `requirement` values: `required`, `conditional` (required in the case named in `when`), `optional`, `not_allowed`, `n/a`.

```json manifest-descriptions
{
  "last_verified": "2026-11-18",
  "documents": {
    "spec_combined": {"provisional": ["Specification", "SPEC", "required", "the combined DOCX is processed as one document; or split it (note 2)"],
                      "nonprovisional": ["Application body structured text document", "", "required", "Patent Center splits it into Specification, Claims, Abstract by heading"]},
    "spec": {"provisional": ["Specification", "SPEC", "required", ""], "nonprovisional": ["Specification", "SPEC", "required", ""]},
    "claims": {"provisional": ["Claims", "CLM", "optional", "claims are optional in a provisional"], "nonprovisional": ["Claims", "CLM", "required", "at least one claim (37 CFR 1.75)"]},
    "abstract": {"provisional": ["Abstract", "ABST", "optional", ""], "nonprovisional": ["Abstract", "ABST", "required", "37 CFR 1.72(b)"]},
    "drawings": {"provisional": ["Drawings-only black and white line drawings", "DRW", "conditional", "when drawings are needed to understand the invention (35 USC 113)"],
                 "nonprovisional": ["Drawings-only black and white line drawings", "DRW", "conditional", "when drawings are needed to understand the invention (35 USC 113)"]},
    "cover_sheet": {"provisional": ["Provisional Cover Sheet (SB16)", "TR.PROV", "conditional", "a cover sheet or an ADS is required (37 CFR 1.51(c)(1))"], "nonprovisional": ["", "", "n/a", "the SB/16 is for provisionals only"]},
    "ads": {"provisional": ["Application Data Sheet", "ADS", "optional", "can serve as the cover sheet; the Patent Center Web ADS needs no upload"],
            "nonprovisional": ["Application Data Sheet", "ADS", "conditional", "needed for benefit or priority claims, an assignee-applicant, or a postponed declaration; the Web ADS needs no upload"]},
    "declaration": {"provisional": ["", "", "n/a", "a provisional needs no declaration"], "nonprovisional": ["Oath or Declaration filed", "OATH", "conditional", "one per inventor; may be postponed (37 CFR 1.53(f)(3))"]},
    "micro_gross_income": {"provisional": ["Certification of Micro Entity (Gross Income Basis)", "MES.GIB", "conditional", "when paying micro entity fees; description not listed for provisionals (note 1)"],
                           "nonprovisional": ["Certification of Micro Entity (Gross Income Basis)", "MES.GIB", "conditional", "when paying micro entity fees"]},
    "micro_education": {"provisional": ["Certification of Micro Entity (Education Basis)", "MES.IHEB", "conditional", "when paying micro entity fees; description not listed for provisionals (note 1)"],
                        "nonprovisional": ["Certification of Micro Entity (Education Basis)", "MES.IHEB", "conditional", "when paying micro entity fees"]},
    "power_of_attorney": {"provisional": ["Power of Attorney", "PA..", "optional", ""], "nonprovisional": ["Power of Attorney", "PA..", "optional", ""]},
    "ids": {"provisional": ["", "", "not_allowed", "no IDS may be filed in a provisional (37 CFR 1.51(d))"], "nonprovisional": ["Information Disclosure Statement (IDS) Form (SB08)", "IDS", "optional", "within the 37 CFR 1.97 windows"]},
    "fee_worksheet": {"provisional": ["Fee Worksheet (SB06)", "WFEE", "optional", "rarely uploaded (note 4)"], "nonprovisional": ["Fee Worksheet (SB06)", "WFEE", "optional", "rarely uploaded (note 4)"]},
    "transmittal": {"provisional": ["Transmittal of New Application", "TRNA", "optional", ""], "nonprovisional": ["Transmittal of New Application", "TRNA", "optional", ""]}
  }
}
```
