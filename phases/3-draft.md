# Phase 3: supported, iterative drafting

Draft the inventor's actual invention, with [examiner review](../references/examiner-review.md) throughout. Claims, specification and figures develop together. Approvals are **versioned checkpoints**, not permanent locks. A changed disclosure or claim requires renewed substantive review and any affected search.

## 1. Resume and settle the material choices

Read the confirmed disclosure, current assessments, prior art, charts and decisions. Identify unresolved risks before drafting. Reuse answers and authorization. A deliberately unsearched or adverse-assessment draft may proceed when the user accepts that basis; label it explicitly, with no implied favorable patentability finding.

Ask only missing consequential questions, two to four at a time:

- Filing type (provisional/nonprovisional/priority claim), territories, target date, prior filings and support, public disclosures/sale/offers/use, and who will file.
- Actual contributors and AI assistance; do not treat an inventor's “yes” to an AI-created mechanism as proof of human conception. Record uncertainty and verify current [inventorship guidance](../references/ai-and-inventorship.md).
- Applicant/assignment, entity status, government funding and correspondence data, only when needed for a filing worksheet. Keep these private in `draft/filing.json`; do not guess.
- Mechanism, actual embodiments, supported alternatives/ranges, best mode and what was tested. Label working versus prophetic examples; never invent results. A prototype is not a universal prerequisite.
- What competitors would copy, observable infringing acts, important claim categories and commercial scope. A usual planning budget is 3 independent/20 total claims; verify current fees instead of assuming that budget fits every matter.

Use [entity status](../references/entity-status.md), [field guides](../references/field-guides/), [forms and filing](../references/forms-and-filing.md), and the filing schema in [state-files.md](../references/state-files.md) as needed. Private directories are outside the installed skill; pass `--dir MATTER` to helpers.

## 2. Draft claims and map support

Use [claim-drafting.md](../references/claim-drafting.md). Draft independent combinations and useful dependent fallbacks in consistent terminology, avoiding accidental divided infringement and unsupported functional breadth. For software, identify the actual technical implementation/improvement, not “AI” pasted onto a desired result.

For each independent claim and meaningful fallback:

1. Map every limitation and required relationship to the user's disclosure in `draft/support-map.md`: claim/limitation → disclosure passage → specification paragraph/figure → fact provenance → gaps.
2. Analyze the **whole combination** against each §102 reference and the strongest supported §103 theory. It is not necessary that an isolated element be individually new. Do not rescue an objection by inventing new features.
3. Apply the strongest examiner objection, supported applicant response, resolution and next action, including §101 and separate §112 concerns where relevant.
4. Explain the protection lost by narrowing and plausible design-arounds. Any model-suggested concept remains a labeled proposal until the inventor supplies/clarifies its actual technical basis; material changes reopen intake/research.

Run `check_claims.py CLAIMS --entity STATUS`. Fix blockers; explain or resolve warnings. Automated word/format checks do not establish substantive support or legal scope.

Show the current claim tree, decisive art, scope tradeoffs and figure plan. Record actual decisions using `state.py decide --gate scope` or legacy `claims`. Legacy `claims_locked`/`figures_locked` flags mean that a version was reviewed; they never forbid revision or establish freshness. Do not force redundant approval of choices already authorized.

## 3. Develop specification and figures together

Use [specification-drafting.md](../references/specification-drafting.md) and the heading/schema contracts in [state-files.md](../references/state-files.md).

- Write the title, cross-references, neutral background, summary, drawing descriptions, detailed embodiments and abstract. Verify applicable formal requirements. Avoid unsupported admissions, scope-limiting boilerplate and invented data.
- Describe structures, steps, algorithms, relationships, meaningful alternatives/ranges and enablement across the intended breadth. Repeating a claim term is not a support analysis. Cover inventor-supported alternatives deliberately; assess claim/continuation strategy and disclosure-dedication risk without a blanket instruction either to disclose everything or to omit all unclaimed embodiments.
- Keep known examples distinct from proposed tests/prophetic examples. Reassess inventorship, priority support and claim scope when the technical disclosure changes.
- Plan `draft/figures.json` so claimed features that need illustration are shown consistently. Use flowcharts, block/sequence diagrams, wireframes, graphs or supplied mechanical views. Do not invent accurate geometry from missing facts; request a sketch/CAD source or flag draftsperson work.
- Maintain `draft/support-map.md` as revisions occur. Show unsupported breadth as an open issue; do not hide it in polished prose.

Run `check_spec.py SPEC --claims CLAIMS --figures FIGURES --filing FILING`. Build with `drawings.py build FIGURES --out OUTPUT`, then run `check_drawings.py`. Visually inspect rendered pages for overlaps, clipping and unreadable numerals. Revise claims, specification or figures whenever the review reveals a substantive problem, then refresh affected checkpoints.

For provisional work, prioritize an enabling description and useful figures. Later claims receive its date only for subject matter it actually supports; a polished provisional or a filing receipt does not guarantee priority for later additions.

## 4. Record current substantive assessment

After final substantive edits, complete a private `draft-assessment.json` from [assessment.json](../templates/assessment.json). Required inputs are disclosure, prior-art record, claims, specification, figures, filing data and support map. Record the exact reviewed scope and the actual user's scope confirmation. For an inconclusive/adverse draft, include `proceed_basis` describing the user's real instruction to continue despite the stated limits.

```sh
python3 /path/to/patentassist/scripts/review.py record --phase draft --input /matter/draft-assessment.json --dir /matter
python3 /path/to/patentassist/scripts/review.py check --phase draft --dir /matter
```

A changed input invalidates this review. Reassess and record a new version; never edit flags/hashes to make a check pass. Computed fee/page totals do not alone invalidate it. The helper verifies fields/source flags/freshness, not truth or legal quality.

## 5. Build and verify the package

1. Complete `draft/filing.json` from actual facts. Use `fill_forms.py worksheet` for required forms; signatures remain blank. Review current forms, fees and filing rules.
2. `build_docx.py --spec SPEC --claims CLAIMS --out OUTPUT --pdf-check` creates document files. Inspect the rendered output.
3. `fees.py estimate` and `ids.py` prepare fee/reference materials. Verify current fees and source disclosure obligations; these are aids, not filings.
4. Run `state.py stale` and `check_package.py --dir MATTER`. Fix blockers and rebuild stale outputs. Package checking requires a **current draft assessment**; an adverse/inconclusive outcome remains an explicit warning even if formats pass.
5. Present current scope, assessment, warnings, open items, files and fee basis. Export with `manifest.py --dir MATTER` when authorized; a package pass is not a grant prediction. Record the package decision without inventing approval.

## 6. Human filing and follow-up

Use [forms-and-filing.md](../references/forms-and-filing.md) to guide Patent Center submission; the human reviews, signs, files and pays. Do not automatically contact the Office or publish the invention.

After actual filing, save the receipt, verify names/title/priority and foreign-filing-license information, record filing dates and use [portfolio.md](../modules/portfolio.md) for deadlines and reminders. Verify each applicable deadline and rule, including priority, IDS, publication/nonpublication and maintenance; a calculated deadline is not a substitute for reviewing the actual filing record.
