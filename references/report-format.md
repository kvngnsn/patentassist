---
title: Direct assessments and source-grounded reports
last_verified: 2026-11-19
sources:
  - https://www.uspto.gov/web/offices/pac/mpep/s2103.html
  - https://www.uspto.gov/web/offices/pac/mpep/s707.html
---

# Report format

Apply [examiner-review.md](examiner-review.md) in every phase. Start with the **current scope and bottom line**, followed by the decisive evidence, strongest examiner objection, strongest supported response, resolution and next action. A source list or per-element chart cannot replace the overall assessment of the combination.

Use conditional favorable/adverse conclusions when supported. Explain the scope, search coverage and remaining uncertainty. No-hit lite searches are not favorable patentability opinions. Phase 0 leaves novelty/obviousness unassessed. Keep FTO, invalidity and patentability in separate sections with appropriate scopes.

## Content order

1. A short deadline/critical-fact notice if one actually affects the next decision; a computed date is a preliminary screen.
2. Bottom line and whether to proceed, clarify, re-search, narrow or stop.
3. Objection → response → resolution, with quoted verified evidence/pinpoints where material. Give 102 and 103 separate reasoning; rank the grounds by importance.
4. Scope and inventor-fidelity changes: what was added/removed, its source, confirmation and protection lost.
5. Supporting charts, closest references, factual/source conflicts, and unresolved questions.
6. Coverage: sources searched/not searched, queries actually run, documents screened/read/cited, unavailable material and stopping reason.
7. Actual decision needed, if not already authorized, and saved review/check paths.

Identify factual provenance as fetched primary source, checked user-supplied document, inference, suggestion or unverified lead. Use source text for quotations; no paraphrases inside quotation marks. State limitations of machine translation and nonofficial pinpoints. A failed or unavailable source supports no decisive claim about what it discloses.

## Concision and audience

Use plain language for inventors; include statute/claim detail for practitioners. Explain an unfamiliar term once. Ask only unanswered consequential questions, two to four at a time. Keep a research-aid/draft note concise; repeat a warning only when circumstances change. Do not bury a bad outlook in caveats or manufacture reassuring “white space.”

Example (illustrative placeholders, not a real assessment): “The current broad formulation is likely obvious over R1 + R2 because [supported rationale]. The strongest answer is [counterargument], but [evidence] defeats it. I would clarify [genuine unresolved feature] before spending on drafting.”

Favorable example after substantial review: “The defined combination appears likely patentable on the reviewed record. R1 lacks [required relationship], and the proposed R1/R2 combination is unsupported because [reason]. [Specific remaining gap] could change that assessment.”

## Local files

Save reports and numbered assessment records in the private matter. `review.py` records `reviews/index.json` and immutable JSON reviews; `state.py` records decisions separately. Do not invent an approval. Keep filing copies free of internal notes; preserve the candid analysis and risks in the private review record. Public-repository packaging never includes real matter directories, caches, contact details or credentials.
