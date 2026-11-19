---
title: US utility patent deadlines (computable)
last_verified: 2026-11-18
sources:
  - https://www.govinfo.gov/content/pkg/USCODE-2023-title35/html/USCODE-2023-title35.htm (35 U.S.C. 21(b) weekend/holiday rule; 119(a), 119(e)(1) and (3); 122(b)(2)(B)(iii); 184)
  - https://www.govinfo.gov/content/pkg/USCODE-2023-title5/html/USCODE-2023-title5-partIII-subpartE-chap61-subchapI-sec6103.htm (5 U.S.C. 6103: list of legal public holidays; Inauguration Day)
  - https://www.ecfr.gov/current/title-37/chapter-I/subchapter-A/part-1 (37 CFR 1.6(a)(4), 1.7, 1.9(h), 1.28(a), 1.29(k), 1.53(f)-(g), 1.55, 1.78, 1.97, 1.102(e), 1.134, 1.136, 1.213(c), 1.311, 1.362, 1.495; eCFR current as of 2026-11-16)
  - https://www.ecfr.gov/current/title-37/chapter-I/subchapter-A/part-41 (41.31, 41.37, 41.41, 41.45, 41.52 appeal timing)
  - https://www.ecfr.gov/current/title-37/chapter-I/subchapter-A/part-90/section-90.3 (63 days to appeal to the Federal Circuit)
  - https://www.uspto.gov/web/offices/pac/mpep/s710.html (MPEP 710.01(a) month arithmetic; 710.02(b) 2-month and 3-month periods; Rev. 01.2024)
  - https://www.uspto.gov/web/offices/pac/mpep/s706.html (MPEP 706.07(f) after-final timing and advisory actions)
  - https://www.uspto.gov/web/offices/pac/mpep/s510.html (MPEP 510: a full-day USPTO closure counts as a federal holiday)
  - https://www.uspto.gov/web/offices/pac/mpep/s601.html (MPEP 601.01(a): missing-parts period "usually two months")
  - https://www.federalregister.gov/d/2024-22481 (89 FR 79899: AFCP 2.0 ended; no requests accepted after Dec 14, 2024)
  - https://www.uspto.gov/sites/default/files/documents/panels-update-sep2026.pdf (Sept 2026 OG notice: Pre-Appeal Brief Conference pilot still running; PTAB judges may join panels)
  - https://www.epo.org/en/legal/epc/2020/r159.html (EPC Rule 159(1): 31 months for European phase entry)
---

# Deadlines

## Rules for computing any date

1. **Months.** A period of N months ends on the **same day-of-month** N months later. If that day does not exist, use the **last day of that month**.
   - Example: Nov 30 + 3 months = Feb 28 (Feb 29 in a leap year).
   - Example: Feb 28 + 3 months = **May 28**, not May 31 (MPEP 710.01(a)).
2. **Days.** "Days" means calendar days, weekends included (1.7(a); MPEP 710.01(a)).
3. **Roll forward.** If the last day falls on a **Saturday, Sunday, or federal holiday within the District of Columbia**, the act is timely on the next business day (35 U.S.C. 21(b); 1.7(a)).
   - The 12-month provisional deadline rolls the same way (35 U.S.C. 119(e)(3); 1.7(b)).
   - Maintenance fee windows roll too (1.362(f)).
4. **Extensions start from the unrolled date.** An extension is added to the **last calendar day of the original period**, not to the rolled-forward date (MPEP 710.01(a)).
   - Example: Jan 31 action + 3 months = Apr 30. A 1-month extension makes it **May 31**, even if Apr 30 was a holiday.
5. **Abandonment** happens after midnight of the last day (MPEP 710.01(a)).
6. **Statutory cap.** No reply to an Office action may be later than **6 months** from the action, with or without extensions (35 U.S.C. 133; 1.134; 1.136(a)). Extensions under 1.136(a) may add **up to 5 months**, but never past that cap.
7. **E-filing date.** A Patent Center filing gets the **Eastern Time** date it is received, **even on a weekend or holiday** (1.6(a)(4)). Filing on a Saturday gets a Saturday date. If a deadline falls on a Saturday, filing on Monday is still timely.

### Which days count as holidays

- **Statutory holidays** (5 U.S.C. 6103(a)):
  - New Year's Day (Jan 1)
  - Birthday of Martin Luther King, Jr. (3rd Monday in Jan)
  - Washington's Birthday (3rd Monday in Feb)
  - Memorial Day (last Monday in May)
  - Juneteenth (June 19)
  - Independence Day (July 4)
  - Labor Day (1st Monday in Sept)
  - Columbus Day (2nd Monday in Oct)
  - Veterans Day (Nov 11)
  - Thanksgiving (4th Thursday in Nov)
  - Christmas Day (Dec 25)
- **Inauguration Day** (Jan 20 every 4th year after 1965) is a holiday for federal employees in the DC area (5 U.S.C. 6103(c)).
- **Observed days.** When a fixed-date holiday falls on a Saturday, the Friday before is the observed holiday for federal employees (6103(b)(1)). When it falls on a Sunday, the Monday after is observed. The Sunday rule comes from an Executive Order, not section 6103 *(unconfirmed: source not checked)*. Treat the observed weekday as a holiday, because the USPTO is closed that day (1.9(h)).
- **Any full-day USPTO closure counts.** 37 CFR 1.9(h) defines "Federal holiday within the District of Columbia" as any weekday the USPTO is **officially closed for the entire day**. That includes weather closures and executive-order closures (MPEP 510).
- **What a script should do:** keep a list of ad hoc closure dates and update it from uspto.gov notices, or call 800-786-9199.
- **Partial closures do not count.** If the USPTO is open for any part of the business day, papers are due that day (MPEP 510).

## Deadline table

"Ext." means extension of time. "Roll" means the weekend/holiday rule applies. Every row rolls except the IDS windows, which are fixed points.

| Event | Deadline | Extendable? | Basis |
|---|---|---|---|
| Provisional filed: file nonprovisional or PCT claiming it | **12 months** from provisional filing | **No.** Restoration by petition if filed within the next **2 months** and the delay was unintentional (1.17(m)(3) fee) | 35 U.S.C. 119(e); 1.78(a)(1), (b); 1.7(b) |
| Benefit claim to provisional in the ADS | Later of **4 months** from nonprovisional filing or **16 months** from provisional filing | No. Late claim by petition (1.78(c)) | 1.78(a)(4) |
| Foreign (Paris) priority: file the US application | **12 months** from the foreign filing (**6 months** for designs) | No. Restoration within **2 months** (1.55(c)) | 35 U.S.C. 119(a); 1.55(b), (c) |
| Foreign priority claim in the ADS | Later of **4 months** from US filing or **16 months** from foreign filing | No. Late claim by petition (1.55(e)) | 1.55(d) |
| Certified copy of the foreign application | Later of **4 months** from US filing or **16 months** from foreign filing | See rule exceptions | 1.55(f) |
| PCT national stage, US | **30 months** from the priority date | **No** ("may not be extended") | 1.495(a), (b) |
| PCT European phase (EPO) | **31 months** from filing or priority date | Not covered here | EPC Rule 159(1) |
| PCT national phase, other offices | Usually 30 or 31 months | *(unconfirmed: check each office)* | |
| Foreign filing without a license | Not before **6 months** after US filing, unless the filing receipt grants a license. No secrecy order may be in place | n/a | 35 U.S.C. 184(a); 37 CFR 5.12; MPEP 140 |
| Nonpublication request then foreign filing: notify the USPTO | **45 days** after the foreign or PCT filing. Missing it abandons the US application | Not extendable (statute) | 1.213(c); 35 U.S.C. 122(b)(2)(B)(iii) |
| Notice to File Missing Parts (nonprovisional or provisional) | Period set in the notice, "usually two months" | Yes, 1.136(a) unless the notice says otherwise | MPEP 601.01(a); 1.53(f)(1), (g)(1) |
| Missing parts when no correspondence address was given | **3 months** from filing (nonprovisional); **2 months** (provisional) | Not stated | 1.53(f)(2), (g)(2) |
| Inventor declaration, when postponed with an ADS | No later than the **issue fee payment** date | **No** | 1.53(f)(3)(ii); 1.136(c) |
| Restriction or election requirement only (no merits action) | **2 months** shortened statutory period | Yes, 1.136(a), up to 6 months total | MPEP 710.02(b); 1.136(a) |
| Ex parte Quayle action | **2 months** | Yes, 1.136(a), up to 6 months total | MPEP 710.02(b) |
| Non-final Office action on the merits | **3 months** shortened statutory period | Yes, 1.136(a), 1-3 months (6 months total max) | MPEP 710.02(b); 1.134; 1.136(a); 35 U.S.C. 133 |
| Final rejection | **3 months**. If the **first reply is filed within 2 months**, the period ends at the later of 3 months or the advisory action's mailing date | Yes, 1.136(a); never past **6 months** from the final rejection | MPEP 706.07(f) |
| Notice of appeal | Within the reply period for the rejection (any claim rejected twice) | Yes, as part of the reply period (1.136(a)) | 41.31(a)(1) |
| Appeal brief | **2 months** from filing the notice of appeal | **Yes** (1.136) | 41.37(a), (e) |
| Appeal forwarding fee | **2 months** from the examiner's answer | **Not under 1.136(a)**; only 1.136(b) for cause | 41.45(a), (c) |
| Reply brief (optional) | **2 months** from the examiner's answer | **Not under 1.136(a)** | 41.41(a), (c) |
| Request for rehearing of a Board decision | **2 months** from the decision | Not under 1.136(a) | 41.52(a), (b) |
| Appeal to the Federal Circuit | **63 days** from the final Board decision | See 90.3(c) | 90.3(a)(1) |
| Notice of Allowance: issue fee (and any publication fee, now $0) | **3 months** from mailing | **No** | 1.311(a) |
| IDS with no statement or fee | Within **3 months** of filing, or before the first merits action, or before the first action after an RCE | **No** extensions | 1.97(b), (f) |
| IDS with statement **or** fee | Before a final action, notice of allowance, or closing action | No | 1.97(c) |
| IDS with statement **and** fee | On or before issue fee payment | No | 1.97(d) |
| Maintenance fee 1 (3.5 years) | Pay from **3 years** to **3 years 6 months** after grant. Grace period with surcharge to the **4th anniversary** | Grace only. After that, petition (1.378) | 1.362(d), (e), (g) |
| Maintenance fee 2 (7.5 years) | **7 years** to **7.5 years**. Grace to the **8th anniversary** | Same | 1.362 |
| Maintenance fee 3 (11.5 years) | **11 years** to **11.5 years**. Grace to the **12th anniversary** | Same | 1.362 |
| Patent expiry for unpaid maintenance fee | End of the 4th, 8th or 12th anniversary of the grant date | n/a | 1.362(g) |
| Small entity refund after paying the full fee | **3 months** from payment | **No** | 1.28(a) |
| Defective micro deficiency paper | **1 month** if the USPTO sets it | **No** | 1.29(k)(3) |
| Track One: cancel excess claims | **1 month** from the first decision on the request | **No** | 1.102(e)(1) |
| Error in an Office action (e.g., wrong citation) | Tell the USPTO within **1 month** to have the period restarted | n/a | MPEP 710.02(b) |

## After-final practice in 2026

- **AFCP 2.0 has ended.** The USPTO accepted no AFCP 2.0 requests filed after **Dec 14, 2024** (89 FR 79899). It had proposed a fee to keep the program. Commenters objected, so the program was allowed to expire. No replacement program was found.
- **Options after a final rejection:**
  - an amendment or argument under 1.116 (entry is not guaranteed)
  - an RCE (1.114; see fees.md)
  - a notice of appeal, optionally with a Pre-Appeal Brief Conference request
- **Pre-Appeal Brief Conference pilot (MPEP 1204.02).** It was still running in Sept 2026. From Sept 10, 2026 a PTAB judge may sit as a third panelist (OG notice, Sept 2026).
- **Reply early.** File the first reply **within 2 months** of the final rejection. That way extension fees are counted from the advisory action date if the advisory action comes after the 3-month date (MPEP 706.07(f)).

## Machine-readable deadline rules

Field meanings:

- `trigger` is the event date the period runs from.
- `offset` uses calendar units.
- `roll: true` applies the weekend/holiday rule to the final day.
- `ext` is the extension type: `none`, `1.136(a)` or `1.136(b)`.
- `max_from_trigger_months` caps the total reply time, extensions included.
- `restore` describes a late-filing safety valve, if one exists.

```yaml
date_rules:
  month_add: "same day-of-month; if missing, last day of month (MPEP 710.01(a))"
  roll: "if final day is Sat, Sun, 5 USC 6103 holiday (observed), or full-day USPTO closure -> next business day (35 USC 21(b); 37 CFR 1.7, 1.9(h))"
  extension_base: "add extension months to the unrolled original final day, then roll (MPEP 710.01(a))"
  efiling_receipt: "Eastern Time date of receipt, weekends and holidays included (37 CFR 1.6(a)(4))"
  holidays_fixed: ["01-01", "06-19", "07-04", "11-11", "12-25"]
  holidays_floating:
    - {name: "MLK Birthday", month: 1, weekday: MON, nth: 3}
    - {name: "Washington's Birthday", month: 2, weekday: MON, nth: 3}
    - {name: "Memorial Day", month: 5, weekday: MON, nth: -1}
    - {name: "Labor Day", month: 9, weekday: MON, nth: 1}
    - {name: "Columbus Day", month: 10, weekday: MON, nth: 2}
    - {name: "Thanksgiving", month: 11, weekday: THU, nth: 4}
  inauguration_day: "Jan 20 every 4th year after 1965 (2029, 2033, ...) (5 USC 6103(c))"
  observed: "fixed holiday on Sat -> Fri; on Sun -> Mon (Sun->Mon rule unconfirmed)"
  ad_hoc_closures: []   # fill from uspto.gov notices; any full-day closure counts

deadlines:
  - {id: provisional_to_nonprovisional, trigger: provisional_filing_date, offset: {months: 12}, roll: true, ext: none,
     restore: {window_months: 2, base: "12-month date (rolled vs unrolled unconfirmed; use unrolled to be safe)", petition: "1.78(b)", fee: petition_restore_priority},
     basis: "35 USC 119(e)(1),(3); 37 CFR 1.78(a)(1), 1.7(b)"}
  - {id: benefit_claim_in_ads, trigger: [nonprovisional_filing_date, provisional_filing_date], offset: [{months: 4}, {months: 16}], combine: later, roll: true, ext: none, basis: "37 CFR 1.78(a)(4)"}
  - {id: paris_priority_us_filing, trigger: foreign_filing_date, offset: {months: 12}, design_offset: {months: 6}, roll: true, ext: none,
     restore: {window_months: 2, petition: "1.55(c)", fee: petition_restore_priority}, basis: "35 USC 119(a); 37 CFR 1.55(b),(c)"}
  - {id: foreign_priority_claim_in_ads, trigger: [us_filing_date, foreign_filing_date], offset: [{months: 4}, {months: 16}], combine: later, roll: true, ext: none, basis: "37 CFR 1.55(d)"}
  - {id: certified_copy_foreign, trigger: [us_filing_date, foreign_filing_date], offset: [{months: 4}, {months: 16}], combine: later, roll: true, ext: none, basis: "37 CFR 1.55(f)"}
  - {id: pct_national_stage_us, trigger: priority_date, offset: {months: 30}, roll: true, ext: none, basis: "37 CFR 1.495(a),(b)"}
  - {id: pct_regional_phase_epo, trigger: priority_date, offset: {months: 31}, roll: "per EPO rules (not modeled)", ext: none, basis: "EPC Rule 159(1)"}
  - {id: foreign_filing_license_wait, trigger: us_filing_date, offset: {months: 6}, roll: false, ext: none, note: "earliest foreign filing without a license; skip if filing receipt grants a license", basis: "35 USC 184(a)"}
  - {id: nonpub_foreign_filing_notice, trigger: foreign_or_pct_filing_date, offset: {days: 45}, roll: true, ext: none, consequence: abandonment, basis: "37 CFR 1.213(c); 35 USC 122(b)(2)(B)(iii)"}
  - {id: missing_parts_notice, trigger: notice_mail_date, offset: {months: 2, source: "as set in notice; usually 2"}, roll: true, ext: "1.136(a)", basis: "MPEP 601.01(a); 37 CFR 1.53(f)(1)"}
  - {id: missing_parts_no_corr_address_nonprov, trigger: filing_date, offset: {months: 3}, roll: true, ext: none, basis: "37 CFR 1.53(f)(2)"}
  - {id: missing_parts_no_corr_address_prov, trigger: filing_date, offset: {months: 2}, roll: true, ext: none, basis: "37 CFR 1.53(g)(2)"}
  - {id: restriction_reply, trigger: action_mail_date, offset: {months: 2}, roll: true, ext: "1.136(a)", max_from_trigger_months: 6, basis: "MPEP 710.02(b)"}
  - {id: quayle_reply, trigger: action_mail_date, offset: {months: 2}, roll: true, ext: "1.136(a)", max_from_trigger_months: 6, basis: "MPEP 710.02(b)"}
  - {id: nonfinal_oa_reply, trigger: action_mail_date, offset: {months: 3}, roll: true, ext: "1.136(a)", max_from_trigger_months: 6, basis: "MPEP 710.02(b); 37 CFR 1.134, 1.136(a); 35 USC 133"}
  - {id: final_rejection_reply, trigger: action_mail_date, offset: {months: 3}, roll: true, ext: "1.136(a)", max_from_trigger_months: 6,
     variable: "if first reply filed within 2 months (rolled), period ends at later of 3 months or advisory action mail date; extension fees then run from that date", basis: "MPEP 706.07(f)"}
  - {id: notice_of_appeal, trigger: action_mail_date, offset: {months: 3, source: "same as reply period"}, roll: true, ext: "1.136(a)", max_from_trigger_months: 6, basis: "37 CFR 41.31(a)(1)"}
  - {id: appeal_brief, trigger: notice_of_appeal_filing_date, offset: {months: 2}, roll: true, ext: "1.136(a)", basis: "37 CFR 41.37(a),(e)"}
  - {id: appeal_forwarding_fee, trigger: examiners_answer_date, offset: {months: 2}, roll: true, ext: "1.136(b)", consequence: "appeal dismissed", basis: "37 CFR 41.45"}
  - {id: reply_brief, trigger: examiners_answer_date, offset: {months: 2}, roll: true, ext: "1.136(b)", optional: true, basis: "37 CFR 41.41"}
  - {id: board_rehearing, trigger: board_decision_date, offset: {months: 2}, roll: true, ext: "1.136(b)", basis: "37 CFR 41.52"}
  - {id: cafc_appeal, trigger: final_board_decision_date, offset: {days: 63}, roll: true, ext: "see 37 CFR 90.3(c)", basis: "37 CFR 90.3(a)(1)"}
  - {id: issue_fee, trigger: notice_of_allowance_mail_date, offset: {months: 3}, roll: true, ext: none, basis: "37 CFR 1.311(a)"}
  - {id: postponed_declaration, trigger: issue_fee_payment_date, offset: {days: 0}, roll: false, ext: none, note: "due no later than issue fee payment", basis: "37 CFR 1.53(f)(3)(ii)"}
  - {id: ids_free_window, trigger: [filing_date, first_merits_action_mail_date], offset: [{months: 3}, {days: 0}], combine: later, roll: false, ext: none, note: "or before first action after RCE", basis: "37 CFR 1.97(b),(f)"}
  - {id: ids_statement_or_fee, trigger: final_action_or_allowance_mail_date, offset: {days: 0}, roll: false, ext: none, note: "must be filed before this date", basis: "37 CFR 1.97(c)"}
  - {id: ids_statement_and_fee, trigger: issue_fee_payment_date, offset: {days: 0}, roll: false, ext: none, note: "on or before", basis: "37 CFR 1.97(d)"}
  - {id: maintenance_1, trigger: grant_date, window_open: {years: 3}, due: {years: 3, months: 6}, grace_end: {years: 4}, roll: true, surcharge_in_grace: maintenance_grace_surcharge, after_grace: "petition 1.378 (1.17(m))", basis: "37 CFR 1.362"}
  - {id: maintenance_2, trigger: grant_date, window_open: {years: 7}, due: {years: 7, months: 6}, grace_end: {years: 8}, roll: true, surcharge_in_grace: maintenance_grace_surcharge, basis: "37 CFR 1.362"}
  - {id: maintenance_3, trigger: grant_date, window_open: {years: 11}, due: {years: 11, months: 6}, grace_end: {years: 12}, roll: true, surcharge_in_grace: maintenance_grace_surcharge, basis: "37 CFR 1.362"}
  - {id: small_entity_refund, trigger: full_fee_payment_date, offset: {months: 3}, roll: true, ext: none, basis: "37 CFR 1.28(a)"}
  - {id: track_one_cancel_excess_claims, trigger: first_decision_on_track_one_request, offset: {months: 1}, roll: true, ext: none, basis: "37 CFR 1.102(e)(1)"}
```

### Extension-of-time lookup for scripts

Compute the last day of an n-month extension as **action mailing date + (shortened period + n) months**, using the month rule above, **then** roll forward (rule 3). This is MPEP 710.01(a): a Jan 31 action with a 3-month period is due Apr 30; a 1-month extension runs to May 31 (Jan 31 + 4 months), not May 30 (Apr 30 + 1 month). Never add months to the rolled date.

A reply needs the smallest n whose extended last day (before rolling) is on or after the reply date, or whose rolled last day is on or after it when the unrolled day fell on a weekend or holiday. Look up the fee as `extension_<n>_month(s)` in fees.md. The 6-month statutory cap (rule 6) still applies.
