---
title: Examiner objections, applicant responses, and candid assessments
last_verified: 2026-11-19
sources:
  - https://www.uspto.gov/web/offices/pac/mpep/s2103.html
  - https://www.uspto.gov/web/offices/pac/mpep/s707.html
  - https://www.uspto.gov/web/offices/pac/mpep/s904.html
  - https://www.uspto.gov/web/offices/pac/mpep/s2111.html
  - https://www.uspto.gov/web/offices/pac/mpep/s2131.html
  - https://www.uspto.gov/web/offices/pac/mpep/s2143.html
  - https://www.uspto.gov/web/offices/pac/mpep/s2145.html
  - https://www.uspto.gov/web/offices/pac/mpep/s2163.html
  - https://www.uspto.gov/web/offices/pac/mpep/s2164.html
---

# Review continuously, not in a final extra phase

Run this pass after the initial brief, significant new evidence, scope decisions and substantive draft changes. The model can perform successive review passes itself; separate agents/models are optional. The procedure below is product design informed by public examination guidance, not an assertion that an AI is an examiner.

## Required output

Lead with the defined scope and overall assessment. Then show the strongest supported objection, strongest supported response, resolution, uncertainty/coverage and next action. Cite evidence where it matters. Do not bury the judgment after ten references. Do not manufacture a response to make both sides look equal. An unpersuasive response should be called unpersuasive.

Acceptable conditional conclusions include “likely anticipated by R1 as currently formulated,” “likely obvious over R1 and R2 for these reasons,” “likely unpatentable at this breadth,” and, after substantial review, “likely patentable within this scope on the reviewed record, subject to these remaining risks.” A statement about the present scope does not condemn every future version of the underlying idea.

No percentages without an independently validated and relevant calibrated model. No guarantees of grant, validity or permission to operate. Inconclusive is appropriate when a specific missing fact, legal issue or search gap prevents resolution, not as the automatic verdict.

| Phase | Assessment boundary |
|---|---|
| 0 | Lead with preliminary readiness or a specific eligibility/disclosure/bar concern, not an overall patentability verdict; novelty/obviousness unassessed. |
| 1 | Decisive verified art can justify a strong adverse assessment. A limited no-hit search supports only “no blocker found in this search.” |
| 2 | Assess proposed claims/combinations as a whole. A supported favorable or adverse assessment is required when the record permits it. |
| 3 | Reassess current claim scope after changes. A draft or passing format checker adds no evidence of patentability. Identify deliberately unsearched drafting as such. |

## Examiner logic and legitimate responses

- **Scope and interpretation:** identify the exact proposed combination or claim version. Use the broadest reasonable construction consistent with the disclosure in the applicable examination setting; do not invent an extreme construction or import omitted limitations. Test whether the objection misunderstands a term or required relationship. [MPEP 2111](https://www.uspto.gov/web/offices/pac/mpep/s2111.html).
- **§102:** identify one qualifying reference teaching every limitation arranged as claimed. Verify prior-art dates/status and exceptions. Inherency requires necessity, not possibility. A missing element, unsupported inherency, different arrangement or inapplicable reference date can defeat the objection. Do not assemble anticipation from multiple unrelated documents. [MPEP 2131](https://www.uspto.gov/web/offices/pac/mpep/s2131.html).
- **§103:** state the relevant scope, differences, skilled-person perspective, rationale to combine/modify, reasonable expectation of success and evidence. Known components alone are insufficient; neither does a novelty distinction automatically defeat obviousness. Test analogous art, teaching away, incompatibility, hindsight, and objective indicia with a nexus when evidence exists. Merely attacking each reference separately may not answer the combination. [MPEP 2143](https://www.uspto.gov/web/offices/pac/mpep/s2143.html), [2145](https://www.uspto.gov/web/offices/pac/mpep/s2145.html).
- **§101 and utility:** address the actual claim as a whole under current law/guidance. “AI,” a generic computer, or a newly imagined technical implementation is not a substitute for analysis. Ask whether the user actually has the asserted mechanism. Check the [current USPTO eligibility page](https://www.uspto.gov/patents/laws/examination-policy/subject-matter-eligibility) and applicable precedent; Office practice and court outcomes can differ.
- **§112:** examine possession/written description, enablement commensurate with scope, and clarity separately. Identify the exact disclosure supporting each limitation; repeated terminology alone proves little. Where a mechanism or breadth is unsupported, ask questions or show a supported narrower choice. Never fill the gap with a claimed mechanism invented by the model. [Written description](https://www.uspto.gov/web/offices/pac/mpep/s2163.html), [enablement](https://www.uspto.gov/web/offices/pac/mpep/s2164.html).
- **Value and fidelity:** ask whether a proposed narrowing still protects what the user cares about. Show the loss of coverage and plausible design-arounds. Do not keep generating weak dependent claims merely to produce a positive result.

Treat statutory bars as fact-sensitive. A calculated anniversary is a screening flag; whether an event triggers a bar, whether an exception applies and what an earlier filing supports require analysis. Compare claims as a combination, not independent legal verdicts for isolated elements.

## Search and evidence

Plan search fields, tools and methods; cover relevant domestic, foreign and nonpatent sources, classify technical functions, inspect full passages/figures, and follow citations. Account for missing sources, failed queries and unpublished material. Do not declare a search complete merely because a fixed query count was reached. [MPEP 904](https://www.uspto.gov/web/offices/pac/mpep/s904.html).

Record the best opposing case, including inconvenient art. A reference must be verified before a decisive conclusion rests on it. Review applicable primary law before treating a digest as current. Provide the reader a concise rationale, not a transcript of internal deliberation.

## Machine-readable review

`templates/assessment.json` defines the fields. `review.py record --phase clarify|lite|deep|draft --input INPUT --dir MATTER` validates and saves a numbered immutable review. `review.py check --phase PHASE --dir MATTER` checks the latest review against current inputs. A changed disclosure/art record invalidates dependent reviews; changed draft files invalidate the draft review. The record contains source-checked references for §102/103 adverse outcomes, not merely a claim that sources were checked.

The checker verifies structure, recorded source flags and hashes. It cannot verify legal reasoning, source truth, inventor confirmation or completeness of a search. Re-run reference/quote checks and substantive review rather than editing flags to obtain a pass. For FTO/invalidity/landscape use `purpose` and a scoped risk assessment; do not relabel that as invention patentability.

## Public teaching and evaluation

[USPTO examiner training](https://www.uspto.gov/learning-and-resources/examiner-training-materials) and [STEPP](https://www.uspto.gov/patents/training/stepp) expose examination methods. The [2016 rejection/response exercise](https://www.uspto.gov/sites/default/files/documents/ai-workshop-iii-spec-clms-wrkshts.pdf) and [answer key](https://www.uspto.gov/sites/default/files/documents/ai-workshop-iii-answer-keys.pdf) are useful teaching structures; refresh their legal analysis before using them as expected answers.

Use complete public file sequences for a later evaluation: dated claims → rejection → response/amendment → next action. Current [ODP File Wrapper](https://data.uspto.gov/apis/patent-file-wrapper/search) and [Office Action Text Retrieval](https://data.uspto.gov/apis/office-action-retrieval/search) require access credentials; legacy Developer Hub endpoints have retired. The historical [Office Action Research Dataset](https://www.uspto.gov/ip-policy/economic-research/research-datasets/office-action-research-dataset-patents) is discontinued and covers 2008–mid-2017. Metadata alone is not an argument corpus.

A proposed 15–30-family evaluation should preserve exact claim versions, blind later outcomes, split by family/time, and score source fidelity, supported objections/responses, resolved judgments and inventor fidelity separately from eventual allowance. Allowed-only samples and interview correlations do not establish causal winning strategies. This public-family evaluation has not been run; local tests use labeled synthetic fixtures.
