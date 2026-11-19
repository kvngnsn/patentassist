# Phase 1: quick prior-art search

**Purpose:** identify decisive obstacles and explain what the evidence means for the user's current invention. A limited no-hit search supports “no blocker found in this search,” not “likely patentable.” Strong verified evidence can support “likely unpatentable as currently formulated.” Apply [continuous examiner review](../references/examiner-review.md) throughout.

All paths below are relative to the private matter directory; scripts are relative to the installed skill. Pass `--dir MATTER` to helpers. Reuse answers and authorization already supplied.

## 1. Resume and confirm scope

Read `state.json`, `invention-disclosure.md`, existing reviews and `prior-art.json`. Run `state.py show --dir MATTER`. Fill missing Phase 0 facts using [0-clarify.md](0-clarify.md). Confirm a plain-language technical brief and its provenance before searching. An inherited brief can satisfy this; do not force redundant intake.

Ask only consequential missing questions, two to four at a time. Confirm search confidentiality once; abstracted functional queries are the default. Record known disclosures, sale/offers, public uses and earlier filings. Unknown is not “none.” A date calculation is only a preliminary screen: verify what happened, applicable exceptions and support in earlier filings before a bar assessment. Never call a calculated anniversary a guaranteed safe filing date.

Break the confirmed invention into elements and **relationships**, with a faithful structural/functional test for each. Removing intended-use language must not invent a mechanism the inventor never described. Store with `prior_art.py elements add E1 "description" --test "supported test" [--essential]`. Record the relevant effective-filing-date assumptions using `prior_art.py cutoff`; own disclosure dates require separate analysis, not an automatic earlier cutoff that excludes intervening art.

## 2. Search and verify

Use [knockout-method.md](../references/knockout-method.md), [search-methodology.md](../references/search-methodology.md) and [sources-and-apis.md](../references/sources-and-apis.md).

1. Plan queries covering functional synonyms, combined features, adjacent technical uses and CPC classifications. Roughly 10–15 queries is a starting budget, not a completeness test. Log queries with `search_log.py plan` and `add`, including rewrites and failed sources.
2. Search public patent sources and nonpatent literature using the host's available retrieval tools. Public Google Patents searches and Crossref/OpenAlex retrieval need no paid patent API. ODP/EPO/Lens are optional when user credentials exist.
3. Fetch promising documents using `patent_fetch.py fetch NUMBER` or `npl_fetch.py`. Read the relevant text, claims and figures; search summaries alone cannot establish content, dates or ownership.
4. Follow backward/forward citations and classifications from the closest references. Read contrary evidence as well as helpful results. Record documents read but not cited with reasons.
5. Map each element and required relationship: explicit / inherent / partial / absent / unknown, plus the actual passage and pinpoint. Use `prior_art.py ref add` and `cell set`. Inherency needs necessity. Tag translations; do not rest a decisive rejection solely on an unchecked machine translation.
6. Run `verify_refs.py` and `quote_check.py`. Resolve blockers before relying on references. These checks support source accounting; they do not determine prior-art status, enablement or legal effect.

If search is unavailable, use supplied art, permitted direct retrieval and citation chains. Offer manual queries at [Google Patents advanced search](https://patents.google.com/advanced). Record every unmet search as a gap; do not fabricate a completed search or infer novelty from retrieval failure.

## 3. Assess the whole formulation

- **§102:** one qualifying reference must disclose every limitation arranged as claimed. Show the mapping, relevant date and any unresolved exception. One decisive reference can support an adverse conclusion without an exhaustive search.
- **§103:** identify the primary reference, actual differences, evidence supporting the modification/combination and reasonable expectation of success. Evaluate the strongest supported response. “All pieces are known” or “obvious pairing” without reasoning is insufficient.
- **§101 / §112 / dates:** reassess issues exposed by the confirmed facts. Explain the strongest objection and response; ask for missing technical facts. Do not add an invented algorithm or sensor to overcome a problem.

For each material issue, report **bottom line → objection → response → resolution → next action**. If the applicant response fails, say why. A possible narrower direction is a question for the inventor, not a feature silently inserted into their invention. Explain whether narrowing preserves commercial value; ask about detectability/trade-secret alternatives when material.

Give a direct overall judgment with scope and limits. Legacy UI labels remain available: `knocked_out` for a supported decisive adverse finding, `crowded` for close art without a resolved knockout, `no_knockout` for no blocker found. These labels do not replace the judgment or support a positive patentability finding. Use `inconclusive` in the structured review when evidence is insufficient.

## 4. Report and checkpoint

Write `reports/lite-report.md` using [lite-report.md](../templates/lite-report.md). Lead with the actual assessment, not the reference list. Include the closest 3–5 sources, useful mapping, strongest combination and response, verified dates, search log/limits and work still owed.

Complete a private copy of [assessment.json](../templates/assessment.json), then:

```sh
python3 /path/to/patentassist/scripts/review.py record --phase lite --input /matter/lite-assessment.json --dir /matter
python3 /path/to/patentassist/scripts/review.py check --phase lite --dir /matter
```

Record `phases.lite` status/date/report/verdict with `state.py set`. Present the consequential choice: deepen the search, investigate a user-confirmed distinction, knowingly draft with search limits, or stop. Honor existing authorization; ask again only for a material new decision. Record actual choices with `state.py decide --gate lite --choice "..." --dir MATTER`.
