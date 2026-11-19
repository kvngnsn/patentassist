---
title: Field guide - chemistry, materials, biotech, and pharma
last_verified: 2026-11-18
sources:
  - url: https://www.ecfr.gov/current/title-37/section-1.831
    supports: 37 CFR 1.831 (applications filed on or after July 1, 2022) Sequence Listing XML required for sequences disclosed by enumeration of residues; thresholds of 4+ specifically defined amino acids or 10+ specifically defined nucleotides (1.831(b)); "SEQ ID NO:" references in description, claims, and drawings (1.831(c)). Text read from eCFR, up to date as of 2026-11-16.
  - url: https://www.ecfr.gov/current/title-37/section-1.832
    supports: 37 CFR 1.832 representation of sequence data in the Sequence Listing XML.
  - url: https://www.ecfr.gov/current/title-37/section-1.833
    supports: 37 CFR 1.833 requirements for a Sequence Listing XML.
  - url: https://www.ecfr.gov/current/title-37/section-1.834
    supports: 37 CFR 1.834 form and format of the Sequence Listing XML submission.
  - url: https://www.ecfr.gov/current/title-37/section-1.835
    supports: 37 CFR 1.835 amendments adding or replacing a Sequence Listing XML (incorporation statement, no-new-matter statement).
  - url: https://www.ecfr.gov/current/title-37/section-1.839
    supports: 37 CFR 1.839 incorporates WIPO Standard ST.26 by reference.
  - url: https://www.ecfr.gov/current/title-37/section-1.821
    supports: 37 CFR 1.821-1.825 older ST.25 rules for applications filed before July 1, 2022.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2412.html
    supports: MPEP 2412 ST.26 requirements; MPEP 2415.02 provisional applications need not include a sequence listing, but any sequence data submitted after July 1, 2022 must be a compliant Sequence Listing XML (37 CFR 1.53(c)(4)); MPEP 2418 WIPO Sequence tool.
  - url: https://www.ecfr.gov/current/title-37/section-1.802
    supports: 37 CFR 1.802(b) deposit needed only when access to the biological material is necessary to satisfy 112.
  - url: https://www.ecfr.gov/current/title-37/section-1.803
    supports: 37 CFR 1.803 acceptable depositories (Budapest Treaty International Depositary Authorities or others the Office recognizes).
  - url: https://www.ecfr.gov/current/title-37/section-1.806
    supports: 37 CFR 1.806 deposit term at least 30 years and at least 5 years after the last sample request.
  - url: https://www.ecfr.gov/current/title-37/section-1.808
    supports: 37 CFR 1.808 access during pendency to those entitled; restrictions irrevocably removed on grant.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s608.html
    supports: MPEP 608.01(p)(II) working vs prophetic examples and tense.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2164.html
    supports: MPEP 2164.01(a) Wands factors, 2164.03 unpredictable arts; Amgen v. Sanofi, 598 U.S. 594 (2023) affirmed enablement analysis for functional antibody genus claims.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2117.html
    supports: MPEP 2117 Markush claims.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2144.html
    supports: MPEP 2144.05 overlapping ranges.
---

# Field guide: chemistry, materials, biotech, pharma

Load at Phase 3, Round 3 (data and examples), Round 4, and Step 3. General rules: `claim-drafting.md`, `specification-drafting.md`. Written description and enablement law: `disclosure-112.md`, `case-law/specification-112.md`. Pharma and biosimilar regimes: `case-law/pharma-and-sep.md`.

## Default claim categories

| Claim | Default | Notes |
|---|---|---|
| Compound or genus (often Markush) | yes for new molecules | structure-based, with species fallbacks |
| Composition / formulation | yes | components with ranges and a weight basis |
| Method of making | yes when the route is new | reagents, conditions, ranges |
| Method of use / treatment | yes for new uses | "administering … to a subject in need thereof" |
| Biological material | sequences, vectors, cells, antibodies | sequence identifiers; deposits if needed |
| Kit | sometimes | components plus instructions |

## What examiners in this field focus on

- **Written description and enablement for genus claims.** Broad functional genus claims ("any antibody that binds X and blocks Y") are the main risk. The spec must let a skilled person make and use the full scope without undue experimentation (Wands factors, MPEP 2164.01(a); Amgen v. Sanofi) and show possession of the genus (`disclosure-112.md`).
- **Obviousness by structural similarity.** Close analogs, homologs, isomers, and salts of known compounds; obvious-to-try reasoning; overlapping ranges (MPEP 2144.05). Unexpected results data is the usual answer.
- **101 for natural products and diagnostics.** Isolated natural products, natural correlations, and diagnostic methods face eligibility rejections (`eligibility-101.md`). Treatment methods with specific steps fare better.
- **Formalities.** Sequence listing compliance, deposit statements, and Markush group form.

## Sequence listings (applications filed on or after July 1, 2022)

| Rule | What to do |
|---|---|
| When required (37 CFR 1.831(a)-(b)) | Any sequence disclosed by listing its residues in order that has 4 or more specifically defined amino acids, or 10 or more specifically defined nucleotides. Shorter sequences must not go in the listing. |
| Format | A "Sequence Listing XML" file in WIPO Standard ST.26 format (incorporated by 37 CFR 1.839). Representation: 1.832. Requirements: 1.833. Form and format: 1.834. |
| References in text | Refer to each listed sequence by identifier ("SEQ ID NO: 1") in the description and claims, even if the sequence also appears in the text. Drawings showing sequences need identifiers in the figure or the Brief Description of the Drawings (1.831(c)). |
| Spec statement | Add the incorporation-by-reference statement naming the XML file, its creation date, and its size in bytes (37 CFR 1.77(b)(5)(ii)). |
| Tool | The USPTO points applicants to WIPO Sequence for building ST.26 files (MPEP 2418). |
| Adding later | An amendment adding or replacing the XML must meet 1.835, including the incorporation statement and a statement that it adds no new matter. Sequences not disclosed at filing cannot be added. |
| Provisional | Not required to include a separate sequence listing. If sequence data is submitted in a provisional filed on or after July 1, 2022, it must be a compliant Sequence Listing XML (37 CFR 1.53(c)(4); MPEP 2415.02). Still disclose every sequence in the text so the provisional supports later claims. |
| Older applications | Applications filed before July 1, 2022 follow the ST.25 rules in 37 CFR 1.821-1.825. |

The skill does not generate ST.26 XML. Tell the user to build it with WIPO Sequence and check it before filing.

## Deposits of biological material

- A deposit is needed only when the material cannot otherwise be made or obtained from the written description, so that access is necessary to meet 112 (37 CFR 1.802(b)).
- Deposit at a Budapest Treaty International Depositary Authority or another depository the USPTO recognizes (1.803).
- Term: at least 30 years, and at least 5 years after the last sample request (1.806).
- Access: available during pendency to those entitled; all restrictions on public access are irrevocably removed when the patent grants (1.808).
- Make the deposit before filing when possible, and put the depository name, accession number, and date in the spec. Ask the user; never invent an accession number.

## Working and prophetic examples

| Kind | Rule |
|---|---|
| Working | Actually performed, with actual results. Past tense. |
| Prophetic | Planned or predicted. Present or future tense. Never state predicted results as obtained (MPEP 608.01(p)(II)). |

- Ask the inventor which data are real. Label each example in notes to the user.
- Unpredictable arts need working examples to support broad claims (MPEP 2164.03). Prophetic examples help show how, but rarely carry a broad genus alone.

## Claim drafting notes

- **Markush groups:** "selected from the group consisting of …" with members that share a property or use (MPEP 2117). Nest groups: broad genus in claim 1, narrower groups and named species in dependents.
- **Ranges:** amounts with units and a basis (wt% of what). Ladder broad → preferred → specific. Support endpoints in the text. Overlap with prior art invites 103; show criticality with data, not adjectives.
- **Transitions:** "comprising" by default; "consisting essentially of" when you must exclude ingredients that would change the basic and novel characteristics, and define those characteristics in the spec.
- **Species fallbacks:** claim the specific compounds, sequences, or formulations the data supports, so a genus rejection still leaves allowable claims.
- **Salts, solvates, polymorphs, stereoisomers:** describe and define them in the spec if they should be covered; claim key forms separately.
- **Treatment claims:** "A method of treating [condition] in a subject in need thereof, comprising administering a therapeutically effective amount of …" Define "effective amount," dosing ranges, routes, and schedules in the spec.

## Figures to include

- Structures and reaction schemes (as figures, or as chemical drawings in the text).
- Graphs of data: dose response, stability, release profiles, yields (label simulated or predicted data).
- Sequence alignments and constructs (with SEQ ID NOs).
- Process flow diagrams for manufacturing.

## Specification must-haves

- [ ] Every compound, sequence, and composition you may claim, with names, structures, or SEQ ID NOs.
- [ ] Genus teaching: the structural features shared by the genus and how they relate to function.
- [ ] Representative species across the genus, with data where available.
- [ ] Ranges with preferred sub-ranges, units, and bases; measurement methods for each property claimed.
- [ ] Methods of making each claimed material, with conditions and alternatives.
- [ ] Methods of use: conditions, subjects, doses, routes, schedules.
- [ ] Working examples (past tense) and prophetic examples (present or future tense), clearly separated.
- [ ] Definitions: "about," "effective amount," "subject," "pharmaceutically acceptable," "consisting essentially of" characteristics.
- [ ] Sequence listing incorporation statement and deposit details if applicable.

## Disclosure traps

- Journal submissions are usually confidential until publication, but posters, preprints, theses, grant reports, and conference abstracts often are not (`bars-and-eligibility.md`).
- Sharing samples or material transfer without confidentiality terms can be a public use or a disclosure.
