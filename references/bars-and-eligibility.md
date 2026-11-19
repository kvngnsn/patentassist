---
title: Statutory bars and the eligibility quick screen (Phase 1, Checks A and B)
last_verified: 2026-11-18
sources:
  - url: https://www.law.cornell.edu/uscode/text/35/102
    supports: 35 U.S.C. 102(a)(1) prior art ("patented, described in a printed publication, or in public use, on sale, or otherwise available to the public"); 102(b)(1)(A)-(B) one-year grace period exceptions for inventor-originated disclosures.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2152.html
    supports: MPEP 2152.02 public use, on sale (Pfaff v. Wells Elecs., 525 U.S. 55 (1998); Helsinn v. Teva, 139 S. Ct. 628 (2019)), otherwise available to the public; one-year grace period extended to the next business day under 35 U.S.C. 21(b).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2153.html
    supports: MPEP 2153.01-2153.02 grace-period exceptions (inventor's own disclosure; intervening disclosure after the inventor's public disclosure); weekend and holiday extension.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2133.html
    supports: MPEP 2133.03(e) experimental use factors; editor note says these sections may apply to AIA applications.
  - url: https://www.epo.org/en/legal/epc/2020/a55.html
    supports: EPC Art. 55 non-prejudicial disclosures (6 months; evident abuse or display at an officially recognized international exhibition; statement and certificate).
  - url: https://www.jpo.go.jp/e/system/laws/rule/other/patent/hatumei_reigai.html
    supports: Japan Patent Act Art. 30 exception to lack of novelty; 1-year period since June 9, 2018; proving document within 30 days of filing.
  - url: https://www.kipo.go.kr/upload/en/download/PatentAct.pdf
    supports: Korea Patent Act Art. 30 (KIPO English text, amended through 2011) - 12 months; excludes the applicant's own laid-open or registered patent publications; claim at filing and prove within 30 days. Secondary sources report a 2015 change allowing later claims in some cases (not confirmed on a primary source).
  - url: https://www.wipo.int/wipolex/en/legislation/details/21027
    supports: China Patent Law amended up to Oct. 17, 2020 (in force June 1, 2021), Art. 24 - six months; four listed situations (public-interest disclosure in a national emergency; first exhibition at a government-sponsored or recognized international exhibition; first publication at a prescribed academic or technological conference; disclosure by another without consent). English text at https://www.wipo.int/wipolex/edocs/lexdocs/laws/en/cn/cn411en_1.pdf.
  - url: scripts/state.py
    supports: compute_bar() - us_last_day = earliest disclosure, sale, offer, or public use + 12 months, rolled past weekends and DC federal holidays; us_status and foreign_status values.
---

# Statutory bars and the eligibility quick screen

Load at Phase 1, Check A (bars) and Check B (eligibility), and whenever a user mentions a disclosure date. `scripts/state.py` computes the clock; this file says what to ask and how to read the result. Full law: `novelty-and-obviousness.md` (102), `case-law/novelty-and-bars.md`, `eligibility-101.md` (101).

## 1. The US bar clock

- Anything public before the effective filing date is prior art: "patented, described in a printed publication, or in public use, on sale, or otherwise available to the public" (35 U.S.C. 102(a)(1)). Worldwide, any language.
- **Grace period (102(b)(1)):** the inventor's own disclosure, or one by someone who got it from the inventor, made one year or less before the effective filing date, is not prior art against the inventor.
- After the inventor's own public disclosure, a third party's later disclosure of the same subject matter is also excluded (102(b)(1)(B)). This shield is narrow; do not rely on it for variations (MPEP 2153.02).
- An independent third party's disclosure is ordinary prior art. It is not a bar question; it goes to Check C.
- **Last safe day** = the earliest disclosure, sale, offer, or public use + 12 months. If that day is a Saturday, Sunday, or federal holiday, it moves to the next business day (35 U.S.C. 21(b); MPEP 2152). `state.py` writes it to `bar.us_last_day`.

| `bar.us_status` | Meaning | Say |
|---|---|---|
| `clear` | no disclosure recorded, or filed before or within the grace period | "File before any disclosure." |
| `clock_running` | disclosure less than a year ago, no filing yet | banner with `bar.us_last_day` in every message |
| `likely_barred` | more than a year passed with no covering filing | knockout under Check A, unless an earlier filing exists; ask |
| `unknown` | dates missing or unreadable | ask for the dates |

## 2. What counts as a disclosure, sale, offer, or public use

| Event | Counts? | Notes |
|---|---|---|
| Journal article, preprint, thesis, poster, talk slides | yes, when publicly accessible | A submission under confidential review is usually not public until publication. A thesis counts once cataloged or indexed. |
| Conference talk or demo | yes | Even without handouts, if the audience was not under confidentiality. |
| Public code repo, package release, app store or public beta | yes | Private repos and closed betas under NDA usually not. |
| Crowdfunding page, product page, social post, video | yes | |
| Trade show display | yes | |
| Investor deck shown without an NDA | likely yes | With an NDA, usually not a public disclosure. |
| Commercial offer for sale, quote, RFP response | yes, if the invention was ready for patenting | Two-part on-sale test (Pfaff v. Wells Elecs.). An offer is enough; no sale needed. |
| Confidential sale to a third party | yes | A secret sale can still be prior art under the AIA (Helsinn v. Teva). An NDA does not stop the clock for sales. |
| Public use by the inventor or others | yes, if not under confidentiality | Includes use in public by customers or testers without restrictions. |
| Experimental use | maybe not | Use controlled by the inventor to test and perfect the invention can negate public use or on-sale activity. The factors come from pre-AIA case law (MPEP 2133.03(e)). Never rely on it without counsel. |
| Filing a patent application | no | Filing is not a disclosure. Publication of the application is, 18 months later. |

Ask about the easy-to-miss channels listed in Phase 1, Step 1, question 3. Save each date with `state.py set dates.<field> YYYY-MM-DD`.

## 3. Foreign grace periods (facts only; confirm with local counsel)

Most countries outside the US apply absolute novelty. A disclosure before the first filing anywhere can destroy novelty there, and a Paris Convention priority claim does not cure it.

| Office | Grace period | Scope | Procedure |
|---|---|---|---|
| Europe (EPC Art. 55) | 6 months before the European filing | Only (a) evident abuse against the applicant, or (b) display at an officially recognized international exhibition. Ordinary publications, talks, and sales are **not** covered. | For exhibitions: state it at filing and file a certificate. |
| Japan (Patent Act Art. 30) | 1 year (since June 9, 2018) | The applicant's own disclosures, and disclosures against the applicant's will | Claim it when filing; file a proving document within 30 days of filing. |
| Korea (Patent Act Art. 30) | 12 months | Disclosures by the person entitled to the patent (not the applicant's own Korean or foreign patent publications), and disclosures against their will | The KIPO English text requires a claim at filing and proof within 30 days; later changes reportedly allow late claims in some cases. Confirm with local counsel. |
| China (Patent Law Art. 24, as amended 2020) | 6 months | Only: first disclosure for the public interest in a national emergency; first display at a government-sponsored or recognized international exhibition; first publication at a prescribed academic or technical meeting; disclosure by another without consent | Declare and prove under the Implementing Rules. Confirm with local counsel. |

Rules for the skill:
- Never tell a user a foreign grace period will save them. Say which rule might apply and recommend local counsel.
- Any public disclosure sets `bar.foreign_status` to `at_risk` or `likely_lost`. Show the foreign-rights banner.

## 4. What the inventor should do now

**No disclosure yet**
1. File before any disclosure. A provisional written at nonprovisional quality is enough to set a date (`filing-paths.md`).
2. Keep using NDAs. An NDA keeps a meeting confidential, which helps keep it from being a public disclosure. It does not set a date, and it does not stop the clock for sales or offers (Helsinn).
3. Hold talks, posts, repos, demos, quotes, and crowdfunding until after filing.

**Already disclosed**
1. File as soon as possible, and no later than `bar.us_last_day`.
2. Record exact dates and keep copies of what was disclosed (slides, posts, archive captures). The filing must cover the disclosed matter and any improvements.
3. Expect foreign rights in absolute-novelty countries to be affected. Get local advice before spending on foreign filings.
4. The inventor's own grace-period disclosure can be identified in the application (optional spec section, 37 CFR 1.77(b)(6)) or shown later by declaration (`novelty-and-obviousness.md`).

**More than a year ago**
- Check A is a knockout unless an earlier filing covers it. Ask once whether any US filing (including a provisional) came first. Improvements made after the disclosure may still be protectable if they are new and not obvious over it.

## 5. Eligibility quick screen (Check B)

Full screen, current USPTO guidance, and cases: `eligibility-101.md`. Flag, never knock out. Six questions:

1. Is the core a process, machine, manufacture, or composition (not a signal, a person, or data alone)?
2. Does the core recite math, a mental process, or a way of organizing human activity (business, finance, advertising, rules)?
3. Does it rest on a natural law, natural correlation, or natural product?
4. If 2 or 3 is yes: does the invention improve how a computer, device, or technical process works, with specific means (not just "do it on a computer")?
5. Is there a particular machine, a specific transformation, or a specific treatment step?
6. US only: the EPO, JPO, and CNIPA use different tests. Do not steer foreign strategy by this screen.

Result: **low** (1 yes, 2 and 3 no; also low when 2 is yes only because the device computes something, and the computation's sole output is a control action on a specific machine, such as changing how a heater, motor, or valve is driven; note it), **medium** (2 or 3 yes, but 4 or 5 clearly yes), **high** (2 or 3 yes, 4 and 5 no or vague). For high, say what technical detail would help.
