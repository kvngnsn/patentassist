# Phase 2: deep research and claim-scope strategy

Use [continuous examiner review](../references/examiner-review.md) after material evidence and scope changes. Assess the **proposed claim combination**, not a collection of novelty verdicts on isolated elements. Provide a candid overall assessment where the record supports one.

All matter paths are outside the skill; pass `--dir MATTER`. Confirm purpose: patentability (default), freedom to operate (FTO), invalidity of specified claims, or landscape. These are different questions and need separate scoped conclusions.

## 1. Resume the actual invention

Read state, confirmed disclosure, reviews, prior art and query log. Reuse completed work. Fill missing Phase 0 facts before invention searches. A quick search is useful but is not a mandatory repeated ceremony when its evidence is already supplied.

Ask two to four consequential questions at a time. Confirm the claimed combination/relationships, user priorities, jurisdictions, relevant dates, prior filings and support, known competitors/art and confidentiality. Effective filing dates can differ by claim or added subject matter; analyze own disclosures and exceptions separately. Do not exclude intervening references merely by using the inventor's earliest disclosure as a universal cutoff. FTO needs territory, product/acts and relevant time; invalidity needs the target claims and their actual priority support.

## 2. Build and run the search

Follow [search-methodology.md](../references/search-methodology.md), [CPC primer](../references/cpc-primer.md) and [source capabilities](../references/sources-and-apis.md).

- Build functional vocabulary and adjacent-use families; store it with `prior_art.py vocabulary set`. Use CPC from fetched records and the classification scheme.
- Plan multiple source types: patent full text/classification, foreign families, backward/forward citations, competing inventors/assignees and nonpatent publications, standards/manuals/products/code where relevant.
- Cover each material feature and its interactions. `search_log.py coverage` is bookkeeping, not proof of completeness. Counts such as 100 screened/25 read are planning estimates, never sufficiency thresholds.
- Fetch with `patent_fetch.py` / `npl_fetch.py`; inspect actual passages, figures, claims and date evidence. A web archive capture can establish availability by that date, not necessarily the first publication date.
- Follow citations from the best references, including examiner citations. Reuse earlier queries; use `search_log.py rerun-plan --since DATE` for changed-date searches. Record read-but-not-cited documents and reasons.
- Run reference and quote checks. Distinguish an authentic document from a legally qualifying, enabling reference. Document access failures, translations, unsearched sources and publication lag.

## 3. Build the strongest objection and answer

For each proposed independent combination and meaningful fallback, provide:

1. Exact scope and reasonable construction, with alternative construction if outcome-determinative.
2. §102 chart against each decisive single reference, including arrangement, necessary inherency, qualifying dates and possible exceptions. Cite passages and figures.
3. §103 theory: primary reference, actual differences, secondary teaching or supported ordinary knowledge, rationale to modify/combine, expectation of success and skilled-person perspective. Address analogous art, incompatibility, teaching away and objective indicia with a nexus where supported. A novel individual component is not required; individually known parts do not by themselves prove obviousness.
4. Strongest supported applicant answer to that actual rejection. Do not answer a combination by attacking each reference in isolation. Unsupported “unexpected results” are a question for evidence, not a finding.
5. Resolution: which argument currently prevails and why; what precise uncertainty prevents a conclusion if unresolved. Apply §101 and separate §112 disclosure/enablement/clarity checks where relevant.

Use `prior_art.py cell set`, `chart.py from-prior-art`, `chart.py render` and combination records. Pinpoints from extracted/translated web text need checking against the official document before filing use. Read pertinent case-law guides as hypotheses to verify against current primary authority.

## 4. Give a useful judgment and scope choice

Lead with “likely unpatentable as currently formulated,” “likely patentable within this defined scope on the reviewed record,” or a specific inconclusive finding. Substantial search plus substantive review is required for a favorable finding. Do not force a positive or balanced result. A likely §102/103 rejection should be stated even when it disappoints the user.

Show broad scope, supported narrower alternatives and the protection lost by each narrowing. For every new feature, identify inventor-provided fact / inference / model suggestion / unknown. Ask whether a proposed distinction actually belongs to the inventor's implementation. A material change reopens Phase 0 and affected searching. Get a version-specific scope choice; preserve the original brief and review history.

## Separate modes

**FTO:** map the relevant product/acts to each potentially enforceable claim in each territory, including construction, remaining term, family/continuations, prosecution and legal-status uncertainty. Analyze direct/divided infringement and supported design-arounds. A patentability finding is not launch clearance; a database status flag is not a legal opinion. Use `templates/fto-screen.md`. Report supported infringement risk, not a guarantee.

**Invalidity:** chart the specified claims and verify claim-specific priority support. Distinguish forum and burden. IPR and ex parte reexamination have patents/printed-publications limits; do not route product/public-use evidence into them as independent statutory grounds. Verify the applicable procedural route and current rules for other grounds/evidence. State likely strengths/weaknesses without pretending a research result is a tribunal decision.

**Landscape:** group themes, CPC, families, assignees and dates; distinguish published filing trends from complete activity. Unoccupied search results are not proof of patentable white space. No invention-patentability verdict is inferred.

## 5. Save and continue

Write `reports/search-report.md` from [search-report.md](../templates/search-report.md), source charts, `prior-art.json`, query coverage and unresolved questions. `ids.py` prepares verified-reference outputs; a practitioner must review disclosure obligations. Word export with `md_to_docx.py` is optional.

Complete `assessment.json`: purpose-specific outcome, grounds, referenced IDs and all objection/response/resolution fields. Record and check with `review.py --phase deep`. Save `phases.deep` status/date/report/purpose/outlook using `state.py`. The structured review, not an isolated outlook sentence, records coverage and freshness.

Confirm any material scope tradeoff with `state.py decide --gate scope`; record next-step choices under `deep`. Existing authorization can cover continuing to drafting. Unresolved substantive questions remain visible in the draft; they must not be silently converted into facts.
