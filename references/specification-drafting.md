---
title: Specification drafting (US utility, provisional and nonprovisional)
last_verified: 2026-11-18
sources:
  - url: https://www.ecfr.gov/current/title-37/section-1.77
    supports: 37 CFR 1.77(b) order of specification sections (13 items, including the prior-disclosure statement and the sequence-listing incorporation statement) and 1.77(c) uppercase headings without bold or underline. Text read from eCFR, up to date as of 2026-11-16.
  - url: https://www.ecfr.gov/current/title-37/section-1.71
    supports: 37 CFR 1.71 detailed description must enable and set out the best mode.
  - url: https://www.ecfr.gov/current/title-37/section-1.72
    supports: 37 CFR 1.72(a) title at most 500 characters, short and specific; 1.72(b) abstract on a separate sheet, preferably at most 150 words.
  - url: https://www.ecfr.gov/current/title-37/section-1.73
    supports: 37 CFR 1.73 summary commensurate with the invention as claimed.
  - url: https://www.ecfr.gov/current/title-37/section-1.74
    supports: 37 CFR 1.74 brief description of the views; detailed description refers to figures by number and parts by numerals.
  - url: https://www.ecfr.gov/current/title-37/section-1.57
    supports: 37 CFR 1.57(c) incorporation by reference must be in the specification and use the words "incorporate" and "reference"; 1.57(d) essential material only from US patents or US published applications; 1.57(b), (h) limits on later fixes.
  - url: https://www.ecfr.gov/current/title-37/section-1.78
    supports: 37 CFR 1.78(a)(3) benefit claim to a provisional must be in the ADS for a nonprovisional.
  - url: https://www.ecfr.gov/current/title-37/section-401.14
    supports: 37 CFR 401.14(f)(4) government support statement wording for federally funded inventions.
  - url: https://www.ecfr.gov/current/title-37/section-1.83
    supports: 37 CFR 1.83(a) drawings must show every claimed feature.
  - url: https://www.law.cornell.edu/uscode/text/35/112
    supports: 35 U.S.C. 112(a) written description, enablement, best mode.
  - url: https://www.law.cornell.edu/uscode/text/35/119
    supports: 35 U.S.C. 119(e) provisional benefit only for what the provisional supports under 112(a).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s608.html
    supports: MPEP 608.01(p)(II) working vs prophetic (paper) examples; prophetic examples not in past tense (Hoffmann-La Roche v. Promega, 323 F.3d 1354 (Fed. Cir. 2003)).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2004.html
    supports: MPEP 2004 item 8, same tense rule for prophetic examples (duty of candor context).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2129.html
    supports: MPEP 2129 statements in the application can be admissions of prior art.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2164.html
    supports: MPEP 2164.01(a) Wands factors, 2164.02 working examples, 2164.03 predictability of the art; Amgen v. Sanofi applied the Wands factors (affirmed, 598 U.S. 594 (2023)).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2165.html
    supports: MPEP 2165 best mode still required in the spec; since the AIA, failure to disclose it is not a ground to invalidate (35 U.S.C. 282).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2181.html
    supports: MPEP 2181 algorithm needed for computer-implemented functions claimed under 112(f).
---

# Specification drafting

Load this at Phase 3, Step 3 (after the claims and figures are locked). The spec exists to support the claims you have and the claims you may need later. Law details: `disclosure-112.md`, `case-law/specification-112.md`. File format and headings: `state-files.md` (`draft/spec.md`). Field specifics: `field-guides/*.md`.

## 1. Section order (37 CFR 1.77(b))

Use uppercase headings with no bold or underline (1.77(c)). Omit a section that does not apply.

| # | Heading | What goes in it |
|---|---|---|
| 1 | TITLE | Short, specific, technical. At most 500 characters (1.72(a)); aim for 15 words or fewer. No "new," "improved," or trademarks. |
| 2 | CROSS-REFERENCE TO RELATED APPLICATIONS | Benefit claims (for example, the provisional's number and date) and an incorporation-by-reference sentence. The legal benefit claim must also be in the ADS for a nonprovisional (1.78(a)(3)). |
| 3 | STATEMENT REGARDING FEDERALLY SPONSORED RESEARCH OR DEVELOPMENT | Only if federally funded. Use the 37 CFR 401.14(f)(4) wording: "This invention was made with government support under [contract number] awarded by [agency]. The government has certain rights in the invention." |
| 4 | THE NAMES OF THE PARTIES TO A JOINT RESEARCH AGREEMENT | Only if a joint research agreement is relied on. |
| 5 | (Incorporation statement for a sequence listing XML, program listing, or large tables) | Only if filed. Name each file, its creation date, and its size in bytes. See `field-guides/chem-bio.md`. |
| 6 | STATEMENT REGARDING PRIOR DISCLOSURES BY THE INVENTOR OR A JOINT INVENTOR | Optional. Identifies the inventor's own grace-period disclosures (`bars-and-eligibility.md`). |
| 7 | BACKGROUND | Field, then the problem. Short. Section 2. |
| 8 | SUMMARY | Tracks the claims in plain words. Section 3. |
| 9 | BRIEF DESCRIPTION OF THE DRAWINGS | One line per figure. Section 4. |
| 10 | DETAILED DESCRIPTION | The body. Sections 5–9. |
| 11 | CLAIMS | Starts on a new page. From `draft/claims.md`. |
| 12 | ABSTRACT | New page. One paragraph, preferably at most 150 words (1.72(b)). Section 10. |

`state-files.md` lists the common headings. When items 5 or 6 apply, add them in this order; if `check_spec.py` does not recognize them, record the WARN as justified.

## 2. Background without admissions

Goal: set the field and the problem. Do not hand the examiner a prior-art admission (MPEP 2129).

Do:
- One paragraph on the field: "The present disclosure relates to [field], and more particularly to [narrower field]."
- One or two paragraphs on the technical problem in neutral terms: what goes wrong, for whom, under what conditions.

Do not:
- Call anything "prior art" or "conventional" unless the user confirms it is someone else's published work, and even then prefer neutral words.
- Describe the inventor's own earlier unpublished work. It may not be prior art at all.
- Disparage named products or references. It can be used against you later.
- Describe the solution. That belongs in the Summary.
- Cite references in the Background as a substitute for an IDS. Known material art goes on the IDS (`forms-and-filing.md`).

## 3. Summary

- Restate each independent claim in plain language, in the claims' order (1.73).
- Use "In some embodiments, …" or "In one aspect, …" for each.
- Add advantages framed as possibilities: "Some embodiments may reduce …" Never promise results every embodiment must achieve.
- Keep it short: a few paragraphs. Do not add features the claims and detailed description lack.

## 4. Brief description of the drawings

One line per figure, in order, matching `draft/figures.json`:

```
FIG. 1 is a block diagram of a system for buffering sensor readings, according to some embodiments.
FIG. 2 is a flowchart of a method of transmitting buffered sensor readings, according to some embodiments.
FIGS. 3A and 3B are perspective views of a clip in an open position and a closed position, respectively, according to some embodiments.
```

Every figure in the drawings appears here, and every figure here appears in the drawings (`check_spec.py`, `check_drawings.py`).

## 5. Detailed description: technique

### Walk the figures
- Describe figures in order. Introduce each element the first time with its numeral: "a base 102."
- Use one numeral series per figure (FIG. 1 → 100s, FIG. 2 → 200s). A numeral means exactly one element across all figures and the text.
- For each element say what it is, what it connects to, and what it does.
- For a flowchart, describe each step by its numeral in order, including decision branches.

### Support every claim term
- Use every claim term word for word at least once. Then describe it more broadly and more narrowly.
- For each construction-dependent term (channel/lumen, module/engine, barb/ridge), give a definition or a list of what it includes.
- Every claimed feature must appear in a figure (37 CFR 1.83(a)).

### Alternatives and variants
Use the variant list from intake (Phase 3, Round 3, question 13). For every element:
- Name the alternatives: materials, mechanisms, algorithms, orders of steps, optional extras.
- Say they can be combined: "Any of the features described for one embodiment may be used in any other embodiment."
- Variant language that works: "In some embodiments, … In other embodiments, … Alternatively, …"

### Ranges
- Give the broad range, then preferred sub-ranges, then specific values: "from 0.2 mm to 1.5 mm, from 0.3 mm to 1.0 mm, or from 0.4 mm to 0.8 mm, for example 0.6 mm."
- Give units and the basis (by weight of what, at what temperature).
- Each claimed endpoint must appear in the spec. A range you may want to claim later needs its endpoints written now.

### Definitions (lexicography)
- You may define a term your own way. Do it clearly: "As used herein, 'X' means …"
- Define only terms that need it. A definition binds you.
- Never define a claim term more narrowly than you want the claim to read.

### Best mode
- Describe what the inventor would actually build or ship today (35 U.S.C. 112(a); 1.71). It must be in the spec, even though failing to disclose it no longer invalidates a patent (MPEP 2165).
- Do not label it "the best mode." Describe it as one embodiment with specific choices.

### Examples: working vs prophetic
| Kind | What it is | Tense |
|---|---|---|
| Working | work actually done, with results actually obtained | past tense ("was mixed," "showed") |
| Prophetic (paper) | planned or predicted work | present or future tense ("is mixed," "will show," "can be expected") |

- Never present a prophetic result as done (MPEP 608.01(p)(II), 2004). It can be a candor problem.
- Label each example's type in your notes to the user, and confirm with the inventor which results are real.

### Software and algorithms
- For every function in the claims, describe how the computer does it: steps, conditions, data structures, and the order of operations. A flowchart with numbered steps plus prose is the minimum. Pseudocode or equations help.
- This is needed for any functional claim language that could fall under 112(f) (MPEP 2181), and it supports the technical-improvement story for 101 (`eligibility-101.md`).
- Describe the hardware context: processor, memory, storage, network, sensors, and where each step runs.
- Describe data structures and formats (fields, keys, message formats) that make the improvement work.
- Details: `field-guides/software.md`.

### Words to avoid
`check_spec.py` flags these. Replace them.

| Avoid | Why | Write instead |
|---|---|---|
| "the invention," "the present invention" | can be read to limit every claim to that description | "the present disclosure," "some embodiments" |
| "critical," "essential," "necessary," "important" | turns a feature into a requirement | "in some embodiments, X provides …" |
| "must," "always," "never," "only," "required" | same | "may," "can," "in some embodiments" |
| "prior art" (for things not confirmed as such) | admission | neutral description |
| "preferred" without alternatives | can narrow | "in some embodiments" plus the alternatives |

### Incorporation by reference
- Use the words "incorporated by reference" and identify the document exactly (1.57(c)).
- Essential material (what supports the claims or enables them) can only be incorporated from a US patent or US published application (1.57(d)). Put anything essential from a paper or website into the text directly.
- Include an incorporation sentence for every priority application at filing. Fixing a missing one later is limited (1.57(b), (h)).

## 6. Enablement scaled to the field

The more predictable the field, the less the spec must show (MPEP 2164.03).

| Field | Typical need |
|---|---|
| Mechanical, simple electrical | Clear structure and how parts fit and move. One or two embodiments plus alternatives often suffice. |
| Software, electronics | Algorithms, data flow, and hardware context in enough detail to build it. |
| Chemistry, biotech, pharma | Working examples, data, and a structure–function link. Broad genus claims need many representative species or a general teaching that lets a skilled person make and use the full scope without undue experimentation (Wands factors, MPEP 2164.01(a); Amgen v. Sanofi, 598 U.S. 594 (2023)). |

Broad functional genus claims in unpredictable fields are the riskiest claims to support. Say so to the user, and draft fallback claims to the species the data actually shows.

## 7. Boilerplate (fresh, short, modern)

Use these as starting points. Adjust to the matter. Keep the total to a few paragraphs; heavy boilerplate is noise.

**Scope and examples**
> The embodiments described here are examples. They do not limit the scope of the claims. Features described for one embodiment may be combined with features of any other embodiment unless the description says they cannot be.

**Terms**
> As used in this disclosure, "a," "an," and "the" include one or more of the item unless the context clearly says otherwise. "Or" is inclusive: "A or B" covers A, B, or both. "Comprising," "including," and "having" are open-ended. "About" and "approximately" mean within plus or minus 10% of the stated value unless another tolerance is stated. "Configured to" means designed, built, or programmed to perform the stated function.

**Computing**
> Operations described as performed by software may be performed by hardware, firmware, or a combination of them. A "processor" may be one or more processing units in one or more devices. "Memory" may be one or more storage devices. A computer-readable medium described here is non-transitory and excludes transitory propagating signals.

**Drawings**
> The figures are not necessarily to scale. Like numerals refer to like elements across the figures.

Change the "about" tolerance if the field uses a different convention, and make sure no definition narrows a claim term you want read broadly.

## 8. Abstract

- One paragraph, preferably 150 words or fewer, on its own page (1.72(b)).
- Summarize what the disclosure covers, mostly from claim 1.
- No claim phrasing ("comprising," "said," "means"), no reference to "the invention," no advantages talk.

## 9. Provisional applications

A provisional gives a filing date for what it describes and enables, and nothing more (35 U.S.C. 119(e)(1); 112(a)). Details and the decision itself: `filing-paths.md`.

- Write it as if it were the nonprovisional. Same sections, same depth.
- Include claims. They are not required (35 U.S.C. 111(b)(2)), but writing them forces you to describe what you will claim.
- Include every variant, range, and alternative you may ever want to claim. A later claim to something the provisional does not describe gets only the later date.
- Include drawings. Every claimed feature should be visible.
- Attaching slides or a paper is better than nothing, but it supports only what it actually discloses. Write the missing details.
- Keep the warning in every provisional output: "Later claims get this date only for subject matter this document describes and enables."

## 10. Final self-review checklist

Run `python3 scripts/check_spec.py patent/draft/spec.md --claims patent/draft/claims.md --figures patent/draft/figures.json --filing patent/draft/filing.json`, fix every BLOCK, then check by eye:

- [ ] Every claim term appears word for word in the detailed description.
- [ ] Every dependent-claim fallback has support, including ranges with exact endpoints.
- [ ] Every negative limitation has explicit support (embodiments without X, and why).
- [ ] Every construction-dependent term is defined or described broadly.
- [ ] Every software function has an algorithm: steps, data, and order.
- [ ] Every claimed feature appears in at least one figure; every figure is described.
- [ ] Every numeral means one element and appears in both the text and the drawings.
- [ ] Best mode is described as an embodiment.
- [ ] Working examples are past tense and real; prophetic examples are present or future tense.
- [ ] No "the invention," "critical," "essential," "must," "always," "only."
- [ ] Background has no admissions and no disparagement.
- [ ] Summary tracks the independent claims and adds nothing they lack.
- [ ] Title at most 500 characters; abstract one paragraph, at most 150 words, no claim phrasing.
- [ ] Funding statement present if funded; JRA parties named if relied on.
- [ ] Incorporation-by-reference sentences present for every priority application; nothing essential incorporated from NPL.
- [ ] Inventorship revisited after claims locked (`ai-and-inventorship.md`).
- [ ] Provisional: the support warning is in the output to the user.
