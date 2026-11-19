# Tool: understand and chart patents

Four jobs: summarize a patent, summarize a file wrapper (estoppel), chart claims (infringement or invalidity), and review someone else's chart. Each starts by fetching the patent with `patent_fetch.py`. Never work from memory of a patent's content.

## A. Patent summary

Input: a number or PDF. Fetch it, then report:
1. **Bibliographic box:** number, kind, title, assignee, inventors, priority, filing, and grant dates, family members, CPC, legal status, and expected expiration. Label each status "as reported by <source> on <date>". Status from Google Patents is an estimate, so check the official record before relying on it.
2. **What problem it solves**, in two to three sentences.
3. **What looks new:** the features the claims add over the background the patent itself describes. Don't characterize the prior art beyond what the patent says.
4. **Each independent claim in plain English:** what someone would have to make, use, or do to infringe. Note "comprising" versus "consisting of", functional language, and any means-plus-function elements (with the spec's corresponding structure).
5. **Key figures and the embodiments** they show.
6. **Weak spots:** vague terms, terms with field synonyms (construction-dependent), possible 101 exposure, a missing algorithm for software functions, and narrow dependents worth noting.

Pinpoint every statement (claim numbers, paragraph labels). Inventor mode: add a glossary of the five most important terms.

## B. File-wrapper (prosecution history) summary

Needs the file wrapper. With `USPTO_ODP_API_KEY` set, list and fetch the documents. Otherwise ask the user to upload them from Patent Center. Then:
1. **Timeline:** filing, publication, each office action (type and date), each reply, interviews, RCEs, appeals, allowance, issue, and continuations in the family.
2. **Per action:** each rejection (statute, references, claims) → the applicant's reply (amendment text and arguments, quoted) → the outcome.
3. **Estoppel and disclaimer map:** every narrowing amendment and every argument distinguishing art. Note which claim term each affects, the words the applicant used, and what scope was likely given up. Mark it as the user's call whether a statement is a clear and unmistakable disclaimer.
4. **Examiner's reasons for allowance,** quoted, with the applicant's response if any.
5. **Terminal disclaimers,** term adjustment, and anything affecting expiration.

## C. Claim chart (infringement or invalidity)

Contracts: `references/state-files.md` → chart@1. Rendering: `scripts/chart.py`.

1. **Gate on purpose and side.** Infringement (our product versus their claim) or invalidity (their claim versus art)? Who does the user represent? A litigation-grade chart needs a matter record and a practitioner. Say so in inventor mode.
2. **Parse the claim** into stably numbered elements `[1pre] [1a] [1b]…`. For each, note the preamble (limiting? "unresolved" unless a construction order exists), the transition, means-plus-function elements (cite the corresponding structure, or flag "no structure disclosed → indefinite risk"), Markush groups, step order, and product-by-process. **Show the parse and get confirmation before mapping.**
3. **Construction check** (load `references/case-law/claims-and-construction.md`; for infringement also `infringement.md` and `defenses.md`; for invalidity also `anticipation.md`, `obviousness.md`, `specification-112.md`). List coined terms, terms defined in the spec, terms narrowed in prosecution (from B if available), "configured to" language, relative terms, and structural nouns with field synonyms. For each, give the reading that makes the mapping work and the one that breaks it. Apply a court's construction if the user has one.
4. **Map.** One row per element and one column per reference or product, with a state, pinpoint, verbatim quote (from fetched or user-supplied text), and a one-sentence analysis.
   - Infringement states: literal / doe / partial / absent / unknown, plus the `construction_dependent` flag. Every literal row that is similar but not identical gets a doctrine-of-equivalents sketch (function, way, result) with an estoppel note, or a stated reason why not.
   - Invalidity states: explicit / inherent / partial / absent / unknown. Do a 102 single-reference check first. Then 103 rows: primary + secondary + motivation sentence. Then a secondary-considerations checklist (commercial success, long-felt need, failure of others, praise, copying), noting whether there's evidence.
   - Dependents asserted means dependents charted. No gestures like "similar for claims 2–9."
5. **No silent supplement.** Thin evidence is `unknown` and goes on the **needs-evidence list**, the most important output. Never infer a product's internals from similar products.
6. **Validate and render:** `chart.py validate`, `quote_check.py`, then `chart.py render --md --csv --docx`. The CSV neutralizes formula characters. Every cell has an unchecked `verified` box; the chart is a lead, not a contention.

## D. Review someone else's chart

Rate each row supported / weak / unsupported. For each weak or unsupported row, give the strongest counter-reading and a rebuttal, and check that the quotes exist in the cited source (`quote_check.py`). Flag missing elements, missing dependents, construction assumptions the chart makes without saying so, and the 102/103 mix-up of using two references for "anticipation."
