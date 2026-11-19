---
title: Field guide - medical devices and diagnostics
last_verified: 2026-11-18
sources:
  - url: https://www.law.cornell.edu/uscode/text/35/287
    supports: 35 U.S.C. 287(c) medical-activity immunity for medical practitioners and related health care entities; exclusions for patented machines, manufactures, compositions, patented uses of compositions, and biotechnology process patents; not applicable to commercial activity regulated under FDA laws (287(c)(3)); only patents from applications with an effective filing date on or after Sept. 30, 1996 (287(c)(4)).
  - url: https://www.ecfr.gov/current/title-42/section-11.35
    supports: 42 CFR 11.35(b) timing of public posting of ClinicalTrials.gov registration information for applicable device clinical trials (devices not previously approved or cleared are posted no earlier than approval or clearance, unless the responsible party authorizes earlier posting).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2106.html
    supports: MPEP 2106 eligibility; Vanda Pharms. v. West-Ward Pharms., 887 F.3d 1117 (Fed. Cir. 2018) (specific treatment method eligible).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2152.html
    supports: MPEP 2152.02 public use and on-sale activity under AIA 102(a)(1); Pfaff two-part on-sale test.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2133.html
    supports: MPEP 2133.03(e) experimental use factors (pre-AIA case law; editor note says it may apply to AIA applications).
  - url: https://www.epo.org/en/legal/epc/2020/a53.html
    supports: EPC Art. 53(c) excludes methods of treatment by surgery or therapy and diagnostic methods practised on the body from patentability in Europe (foreign note only).
---

# Field guide: medical devices and diagnostics

Load at Phase 3, Round 4 and Step 3, and at Phase 1 Check A when the user mentions trials, FDA submissions, or hospital evaluations. General rules: `claim-drafting.md`, `specification-drafting.md`. Device software also uses `field-guides/software.md`. Diagnostics and drug-delivery chemistry also use `field-guides/chem-bio.md`.

## Default claim categories

| Claim | Default | Notes |
|---|---|---|
| Device / system | yes | the main asset; structure and operation |
| Device-side method of operating | yes | steps performed by the device's controller (one actor: the device) |
| Method of manufacture | when the process is new | |
| Kit | sometimes | device plus consumables or tools |
| Surgical or treatment method performed by a clinician | only as a secondary claim | limited remedies against practitioners (below) |

## Medical-procedure immunity: 35 U.S.C. 287(c)

- A patent owner gets no remedies (no damages, injunction, or fees) against a licensed medical practitioner, or the related health care entity, for performing a "medical activity" that infringes under 271(a) or (b).
- "Medical activity" means performing a medical or surgical procedure on a body. It does **not** include:
  - using a patented machine, manufacture, or composition of matter in violation of the patent;
  - practicing a patented use of a composition of matter;
  - practicing a process in violation of a biotechnology patent.
- It does not protect commercial makers and sellers of FDA-regulated products (287(c)(3)).
- It applies to patents from applications with an effective filing date on or after September 30, 1996 (287(c)(4)).

**Drafting consequence:** a pure surgical-technique claim ("making an incision at … and inserting …") may be unenforceable against the surgeons who practice it. Claim the device, the device-side method, and the kit, so the maker and seller are the infringers. Keep a technique claim as a secondary claim if it adds value.

Outside the US: Europe excludes methods of treatment by surgery or therapy and diagnostic methods practiced on the body (EPC Art. 53(c)). Device claims are the portable asset. Recommend local counsel for foreign strategy.

## Eligibility (101) notes

- Devices: low risk.
- Specific treatment methods (administer X at dose Y to a patient with condition Z) have been held eligible (Vanda v. West-Ward, 887 F.3d 1117 (Fed. Cir. 2018)).
- Diagnostics that detect a natural correlation and add only routine steps are high risk. Details and current guidance: `eligibility-101.md`.
- Software as a medical device: treat as software (`field-guides/software.md`).

## FDA timing vs public disclosure

Regulatory work creates public records and public uses. File before any of these become public.

| Activity | Disclosure risk | What to do |
|---|---|---|
| 510(k), De Novo, or PMA decision | FDA publishes decisions and summaries after clearance or approval | File before clearance; the summary can describe the device in detail |
| Clinical trial registration | Registration information becomes public on ClinicalTrials.gov. For a device not previously approved or cleared, posting comes no earlier than approval or clearance unless the sponsor authorizes earlier posting (42 CFR 11.35(b)) | Check what the entry says and when it will post; assume it will become public |
| Trial use on patients | Use outside a confidential, controlled protocol may be public use | Keep confidentiality agreements with sites and investigators; document control |
| Experimental use | Can negate public use when the inventor controls testing to perfect the invention (MPEP 2133.03(e)); built on pre-AIA case law | Never rely on it without counsel |
| Hospital evaluations, sample units, pricing quotes, distributor talks | Offers for sale and sales can bar the patent, even confidential ones (Helsinn; `novelty-and-obviousness.md`) | File before quoting or shipping; check every offer date |
| Conference abstracts, posters, investor decks | Printed publications or public disclosures | File first; NDAs keep secrets but do not stop the clock |

Add each date to `state.json → dates` so `state.py` computes the bar clock (`bars-and-eligibility.md`).

## What examiners in this field focus on

- **103 over known device platforms.** Catheters, stents, and wearables are crowded. Tie the novelty to a specific structure or control behavior.
- **Functional language.** "configured to deliver therapy" is met by any capable device (MPEP 2114). Claim the structure or the control algorithm.
- **Relative terms.** "flexible," "atraumatic," "small diameter" need numbers or definitions.
- **Diagnostic method claims.** 101 rejections.

## Figures to include

| Figure | Use |
|---|---|
| Perspective and exploded views | device structure (from the user's CAD) |
| Sectional views | lumens, layers, internal mechanisms |
| Placement in anatomy | where and how the device sits (schematic line art) |
| Block diagram | electronics, sensors, therapy delivery |
| Flowchart | control algorithm and device-side method |
| Graphs | measured performance (label bench, animal, or clinical data) |

## Specification must-haves

- [ ] Device structure with materials, including biocompatible options and coatings.
- [ ] Dimensions as ranges with units (lengths, diameters in mm or French size, wall thicknesses).
- [ ] How it is used, step by step, including anatomical sites and alternatives, so method-of-use claims are supported even if not claimed now.
- [ ] Control algorithms for any powered or software function (steps, thresholds, timing).
- [ ] Sensing and therapy parameters with ranges (pressure, flow, energy, frequency).
- [ ] Sterilization, packaging, and kit contents if claimable.
- [ ] Data: bench, animal, or clinical, each labeled, past tense only if done.
- [ ] Definitions: "subject," "distal," "proximal," "atraumatic," "lumen" vs "channel."
