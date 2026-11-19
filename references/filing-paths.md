---
title: Filing paths - provisional, nonprovisional, Track One, PCT first
last_verified: 2026-11-18
sources:
  - url: https://www.law.cornell.edu/uscode/text/35/111
    supports: 35 U.S.C. 111(b) provisional filing; claims not required (111(b)(2)); abandoned after 12 months unless converted (111(b)(5)).
  - url: https://www.law.cornell.edu/uscode/text/35/119
    supports: 35 U.S.C. 119(e)(1) benefit of a provisional only for an invention disclosed in it as 112(a) requires (best mode excepted), filed within 12 months; 119(a) Paris priority.
  - url: https://www.law.cornell.edu/uscode/text/35/122
    supports: 35 U.S.C. 122(b) publication at 18 months; provisionals not published; nonpublication request at filing with certification; 45-day notice after a foreign filing or the application is abandoned.
  - url: https://www.law.cornell.edu/uscode/text/35/154
    supports: 35 U.S.C. 154(a)(2)-(3) term from the earliest US nonprovisional filing; provisional priority not counted; 154(d) provisional rights after publication.
  - url: https://www.law.cornell.edu/uscode/text/35/184
    supports: 35 U.S.C. 184 foreign filing license needed before filing abroad within 6 months of US filing for an invention made in the US.
  - url: https://www.ecfr.gov/current/title-37/section-1.53
    supports: 37 CFR 1.53(c) provisional filing date with or without claims; 1.53(c)(3) converting a provisional measures term from the provisional date (USPTO advises claiming benefit instead).
  - url: https://www.ecfr.gov/current/title-37/section-1.78
    supports: 37 CFR 1.78(a) 12-month window; 1.78(b) restoration of provisional benefit when the delay was unintentional (petition, within 14 months).
  - url: https://www.ecfr.gov/current/title-37/section-1.102
    supports: '37 CFR 1.102(e) Track One: original nonprovisional, complete at filing, at most 4 independent / 30 total claims, no multiple dependent claims.'
  - url: https://www.ecfr.gov/current/title-37/section-1.213
    supports: 37 CFR 1.213 nonpublication request, rescission, 45-day notice of foreign filing.
  - url: references/fees.md
    supports: All fee amounts, Track One fees and annual cap, continuing-application fees.
---

# Filing paths

Load this at Phase 3, Round 1, question 1, or whenever the user asks "provisional or nonprovisional?" US utility only. Fee numbers are in `fees.md` and `scripts/fees.py`; deadline math is in `deadlines.md` and `scripts/deadlines.py`; forms are in `forms-and-filing.md`. Do not restate fee amounts here.

## 1. Decision table

| Situation | Usual path | Why |
|---|---|---|
| First filing, still changing the design, limited budget | Provisional, written at nonprovisional quality | Low cost, buys a date, 12 months to refine and decide |
| Disclosure or launch coming soon, no time for a full draft | Provisional now, as complete as time allows | A date before the disclosure protects foreign options and avoids the US clock |
| Already disclosed publicly, US grace clock running | File before `bar.us_last_day`; provisional is fine | The 102(b)(1) grace period protects only a filing made within one year (`bars-and-eligibility.md`) |
| Design is stable and a patent is wanted soon | Nonprovisional (optionally with Track One) | Examination starts now; no 12-month detour |
| Patent needed fast (investors, licensing, enforcement) | Nonprovisional with Track One | Prioritized examination; higher fees and claim limits (Section 4) |
| Foreign markets matter and the US is not the urgent market | US provisional, then PCT within 12 months; or PCT first | Keeps foreign options open up to 30/31 months from priority (Section 5) |
| Will never file abroad and wants secrecy until grant | Nonprovisional with a nonpublication request at filing | Application stays unpublished (Section 6) |
| Provisional already on file, 12 months nearly up | Nonprovisional (and/or PCT) claiming its benefit | Missing the date loses the benefit; restoration is narrow (Section 2) |

Ask before recommending: budget, timing of any disclosure or launch, foreign markets, whether the design is final, and whether a fast patent matters.

## 2. What a provisional does and does not do

**Does:**
- Gets a US filing date for what it describes and enables (35 U.S.C. 111(b); 119(e)).
- Lets the user say "patent pending."
- Starts a 12-month window to file a nonprovisional or PCT that claims its benefit (37 CFR 1.78(a)).
- Keeps the 20-year term clock from starting: term runs from the nonprovisional filing, not the provisional (35 U.S.C. 154(a)(3)).
- Accepts any format: no claims required (111(b)(2)), no oath, no IDS.

**Does not:**
- Get examined, or ever become a patent by itself.
- Get published on its own (35 U.S.C. 122(b)). It becomes visible later only through an application that relies on it.
- Support later claims beyond what it discloses. A later claim to an undescribed variant gets the later date (119(e)(1); `disclosure-112.md`).
- Last past 12 months. It is abandoned after that (111(b)(5)).
- Claim the benefit of another provisional.

**Notes:**
- Several provisionals can be claimed by one nonprovisional if each is within 12 months of it. The earliest one sets the deadline.
- Restoration: if the 12-month date is missed unintentionally, a petition can restore the benefit within 2 more months (37 CFR 1.78(b)). Docket it, but never plan on it.
- Converting the provisional itself into a nonprovisional is possible (37 CFR 1.53(c)(3)), but the patent term is then measured from the provisional date. File a new nonprovisional that claims benefit instead.
- Docket the 12-month date with reminders at 9 and 11 months (`deadlines.py`).

**The warning to give every time a provisional is chosen:**
> A provisional buys a date only for what it actually describes and enables. A thin provisional buys very little.

## 3. Nonprovisional

- Examined. Needs claims, the inventor's oath or declaration (can be postponed with an ADS; see `forms-and-filing.md`), and filing, search, and examination fees.
- Published about 18 months from the earliest priority date unless a nonpublication request was made at filing.
- Can claim the benefit of the user's provisional (benefit claim goes in the ADS, 37 CFR 1.78(a)(3)).
- Claim fees apply over 3 independent / 20 total (`claim-drafting.md`, `fees.md`).
- The IDS duty starts (`forms-and-filing.md`).

## 4. Track One (prioritized examination)

- Request with an original utility nonprovisional, filed electronically and complete at filing (37 CFR 1.102(e)).
- Limits: at most 4 independent claims, 30 total, and no multiple dependent claims.
- The USPTO aims for a final disposition within about twelve months (`fees.md` cites the program page).
- Extra fees and an annual cap on requests: see `fees.md`.
- Not available for provisionals, design applications, or PCT applications before national stage.
- Good fit: stable design, a reason to want the patent soon, budget for the fee.

## 5. Foreign filing basics (facts only; recommend local counsel)

This skill drafts US applications only (SKILL.md US-utility scope). Give these facts and refer foreign strategy to counsel.

| Point | Fact |
|---|---|
| Paris Convention priority | 12 months from the first filing to file abroad and claim its date. |
| PCT | One international application filed within 12 months of the priority date; national or regional phase entry generally at 30 months from priority (31 at some offices, including the EPO). It never becomes a patent by itself. |
| Absolute novelty | Most countries outside the US have no general grace period. Any public disclosure before the first filing can destroy novelty there. Details: `bars-and-eligibility.md`. |
| Foreign filing license | For an invention made in the US, filing abroad within 6 months of the US filing needs a license (35 U.S.C. 184). The US filing receipt usually shows whether one was granted. Details: `forms-and-filing.md`. |
| US-only doctrine | Never apply US law (101, grace period, claim rules) to another office. |

Deadline facts for foreign and PCT dates: `deadlines.md`.

## 6. Nonpublication request: the trade-off

A nonpublication request keeps a nonprovisional unpublished until it issues (35 U.S.C. 122(b)(2)(B); 37 CFR 1.213).

| For | Against |
|---|---|
| The invention stays secret if the application is abandoned or rejected, so trade-secret protection may survive | Must be made **at filing**; it cannot be added later |
| Competitors cannot read the application during examination | The applicant certifies it will not file abroad in a country that publishes at 18 months. If it later does, it must tell the USPTO within 45 days or the application is abandoned (37 CFR 1.213(c)) |
| | No provisional rights (reasonable royalty for the period between publication and grant, 35 U.S.C. 154(d)) because nothing is published |
| | It can be rescinded at any time, but the foreign plan should be decided first |

Recommend it only when the user is sure there will be no foreign filing and secrecy has real value.

## 7. Continuations and continuations-in-part (awareness only)

| Type | What it is | Key rule |
|---|---|---|
| Continuation | New application, same disclosure, new claims | Must be filed while the parent is still pending (35 U.S.C. 120). Lets the owner pursue claims aimed at competitors' products later. |
| Divisional | Continuation filed to pursue claims the examiner restricted out | Same copendency rule (35 U.S.C. 121). |
| Continuation-in-part (CIP) | Parent disclosure plus new matter | New matter gets only the CIP's filing date. The term still runs from the earliest nonprovisional in the chain (154(a)(2)), so a CIP does not extend term. |

- Keeping one continuation pending is a common strategy for valuable patents. Raise it at allowance.
- Continuing applications carry extra fees in some cases (`fees.md`).
- The skill does not draft continuations or CIPs in v1. Point the user to a practitioner.

## 8. When to bring in a registered practitioner

Say this once, plainly, and let the user decide (`practitioner-rules.md`):
- Filing for someone else's invention. That is practice before the USPTO and needs registration (37 CFR 11.5, 11.10).
- The patent is central to fundraising, licensing, or a likely dispute.
- A crowded field where claim scope will decide value.
- Chemistry, biotech, or pharma genus claims, or anything relying on data.
- Foreign filing strategy, PCT national phase choices, or a nonpublication decision.
- A final rejection, appeal, restriction strategy, or interference with a competitor's filing.
- Any FTO or launch decision.

Free and low-cost help (USPTO Pro Se Assistance Center, Patent Pro Bono Program, law school clinics) is listed in `practitioner-rules.md`.
