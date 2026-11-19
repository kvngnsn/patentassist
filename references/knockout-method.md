---
title: Knockout search method (Phase 1, Check C)
last_verified: 2026-11-18
sources:
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2131.html
    supports: MPEP 2131 (one reference, every element, arranged as claimed; not an ipsissimis verbis test), 2131.02 (genus and species; "at once envisage", Kennametal v. Ingersoll, 780 F.3d 1376 (Fed. Cir. 2015)), 2131.03 (anticipation of ranges). MPEP 9th Ed., Rev. 01.2024 is current per the MPEP index page.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2112.html
    supports: MPEP 2112 inherency (necessarily present, not probably present).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2121.html
    supports: MPEP 2121 prior art presumed operable and enabling; rebuttable.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2125.html
    supports: MPEP 2125 drawings as prior art; must show all claimed structure and how it fits together.
  - url: https://www.law.cornell.edu/uscode/text/35/102
    supports: 35 U.S.C. 102(a)(1), 102(a)(2), 102(b)(1), 102(d) (what counts as prior art and as of when).
  - url: references/sources-and-apis.md
    supports: Which sources are keyless, robots.txt limits on Google Patents, Wayback dating rule.
  - url: references/state-files.md
    supports: prior-art.json fields, element states, prior_art_basis values.
---

# Knockout search method

Load this at Phase 1, Check C. The goal is narrow: find one reference that already has every element, or show that a cheap search found none. Use 10–15 queries as a planning budget, not a completeness threshold or time promise. Apply `examiner-review.md` to resolve both anticipation and supported obviousness theories.

Law for the verdict lives in `novelty-and-obviousness.md` and `case-law/anticipation.md`. Dates and bars live in `bars-and-eligibility.md`. Sources and endpoints live in `sources-and-apis.md`.

## 1. Inputs you need before the first query

- [ ] Elements `E1..En` confirmed and saved in `prior-art.json → elements`, with 1–2 marked `essential`.
- [ ] `state.json → profile.confidentiality` read: `abstracted` (default) or `detailed`.
- [ ] Cutoff date set (`prior-art.json → cutoff_date`): the relevant effective-filing-date assumption, analyzed by claim/support when needed. Treat own disclosures and exceptions separately; do not automatically exclude intervening art.
- [ ] Known art from intake fetched first with `patent_fetch.py` (it is free coverage and often the closest art).
- [ ] The one-time notice given: public search sites can log queries.

## 2. Plan 10–15 queries from the elements

Write the plan into `prior-art.json → queries` before running it. Each query names the elements it targets.

**Building rule:** every query = the essential element + one or two other elements. Never put all elements in one query. That over-constrains the search, and in abstracted mode the full combination is the secret.

Default mix for 12 queries:

| # | Type | Source | What it does |
|---|---|---|---|
| 1–3 | Core combinations | available web search `site:patents.google.com` | essential element + a different second element each time |
| 4–5 | Synonym swap | available web search `site:patents.google.com` | same pairs, field vocabulary or older names |
| 6 | Functional phrasing | available web search `site:patents.google.com` | what the element does, not what it is called |
| 7–8 | CPC-anchored | available web search `site:patents.google.com` | CPC code string + one or two keywords (Section 3) |
| 9–10 | Products and manuals | plain available web search | product pages, manuals, videos, crowdfunding pages, teardown blogs |
| 11–12 | Papers | `npl_fetch.py search "…"` | Crossref then OpenAlex |
| + | ODP search | `USPTO_ODP_API_KEY` only | skip if no key |

Citation hops (Section 6) do not count against the query budget.

Log every query: `python3 scripts/search_log.py add …` with source, string, hit count, how many you screened, and elements targeted.

## 3. available web search patterns for `site:patents.google.com`

Search engines vary in which operators they honor. Treat every operator as a hint, and always check the fetched record's dates yourself.

| Need | Pattern | Notes |
|---|---|---|
| Exact phrase | `"turn signal"` | Quote two- or three-word technical phrases. Do not quote whole sentences. |
| Alternatives | `"turn signal" OR "direction indicator"` | Write `OR` in capitals. Keep each OR group to 2–4 terms. |
| Required pair | `helmet "turn signal" wireless` | Plain words are ANDed by default. |
| Exclude noise | `-toy -costume` | Use sparingly. Excluding can drop a real reference that mentions the word once. |
| Date limit | `before:2020-01-01` or `after:2015-01-01` | Honored by some engines, ignored by others. The page date it filters on is not the priority date. Always confirm `priority_date` in the cached record. |
| CPC anchor | `"A42B3/0433" "turn signal"` | Google Patents pages print CPC codes without the space (`A42B3/0433`). Quoting the code string finds pages that carry that classification. Heuristic only. |
| Patent PDFs | `site:patentimages.storage.googleapis.com …` | Useful for older documents whose HTML text is thin. |
| Products | drop `site:`; add `manual`, `datasheet`, `kickstarter`, `teardown`, `review` | Products need a provable date (Section 5). |

Good query (abstracted): `site:patents.google.com helmet ("turn signal" OR "direction indicator") wireless handlebar`

Bad query: `site:patents.google.com smart helmet with rear LED turn signals controlled by a Bluetooth handlebar remote that auto-cancels using an accelerometer`. It is too long, it leaks the whole invention, and it returns only near-verbatim matches.

Do not call Google Patents' `xhr/query` endpoint or fetch its search-results pages; robots.txt disallows them (`sources-and-apis.md`). If the user wants to browse, give them `https://patents.google.com/advanced` and let them run the query in their own browser.

## 4. Abstracted vs detailed wording

`abstracted` (default) means queries describe function and generic structure. `detailed` means the user allowed specific technical terms. Neither mode ever sends the disclosure text, code, names, or customer data.

**Abstraction rules (abstracted mode):**
1. Describe what a part does in common field words.
2. Drop exact numbers, thresholds, ranges, model names, coined terms, product names, and code identifiers.
3. Split the combination: no single query carries more than three elements.
4. Prefer the broader term (genus) over the inventor's specific choice (species).
5. Never paste a sentence from the disclosure, even a short one.

| Confidential feature (never sent) | Abstracted queries (sent) |
|---|---|
| "Our LSTM predicts when each scooter needs a battery swap from GPS and motor-current logs, 15 minutes ahead" | `"electric scooter" "battery swap" predict` · `fleet vehicle "state of charge" forecast route` |
| "PEEK clip with a 0.4 mm living hinge snaps onto a 22 mm handlebar" | `handlebar clip "living hinge"` · `snap-fit mount handlebar polymer` |
| "Adaptive rate limiter that keys on the TLS fingerprint and drops the token bucket refill rate by 40% for repeat offenders" | `rate limiting client fingerprint "token bucket"` · `adaptive throttling repeat requests fingerprint` |
| "Peptide KLWVRAF fused to a PEG-12 linker for blood–brain barrier transport" | `peptide linker "blood-brain barrier" transport conjugate` (never send the sequence) |

**Detailed mode:** you may use the specific terms (`"living hinge" PEEK handlebar`). Still split the combination, and still never send code, names, or the disclosure verbatim.

Fetching a known patent by number is always fine in either mode.

## 5. Screening: three passes

Screen many cheaply, read few closely.

| Pass | Read | Decide | Record |
|---|---|---|---|
| 1. Snippet | title, snippet, CPC in the result | Could it show the essential element? If no, drop. | count in the query's `screened` |
| 2. Claims + abstract | fetch with `patent_fetch.py`; read abstract and independent claims; scan the figure list | Does it show the essential element plus at least one other? If no, drop with a reason. | drops go to `read_not_cited` with one line |
| 3. Description | search the cached `description` for each element's vocabulary; read the matching paragraphs and figures | State per element, pinpoint, verbatim quote | `element_map` in `prior-art.json` |

Pass 3 rules:
- Read the paragraphs, not just the hit sentence. A word match is not a disclosure.
- Use the five states: `explicit`, `inherent`, `partial`, `absent`, `unknown`. If you did not read enough, the state is `unknown`, never `absent`.
- Quote exact words from the cached text. `quote_check.py` will reject anything else.
- Mark `construction_dependent: true` when the match turns on how a common structural word is read (channel or lumen, barb or ridge, terminal or contact, module or engine).
- Dates come from the cached record. `verify_refs.py` sets `prior_art_basis` against the cutoff. Do not eyeball it.
- Products and web pages: date them with `npl_fetch.py wayback URL`. A Wayback capture proves the page existed no later than the capture time. No provable date means `needs_evidence`, and it cannot support a knockout.
- Abandoned applications still count as printed publications once published.

## 6. Citation hop (cheap and high-yield)

Do this for the two closest references after Pass 3.

1. Open their cached `citations.backward` and `citations.forward`.
2. Sort examiner-cited entries (`examiner: true`) first. Examiners cite what they think is closest.
3. Add citations listed on family members' records (`family`), since examiners often cite different art in different offices.
4. Screen titles (Pass 1). Fetch the best three. Run Passes 2–3 on them.
5. Log the hop as a note in `audit.jsonl`; it does not use the query budget.

## 7. When to stop

Stop at the first of these:
1. **Knockout verified.** One reference passes every test in Section 8, `verify_refs.py` and `quote_check.py` pass, and every element is quoted.
2. **Budget spent.** 15 queries plus the citation hop.
3. **Saturation.** Two query rounds in a row (about 4 queries) surfaced no new candidate with the essential element plus one other element. Note "stopped at saturation" in the coverage block.

Always report all three Phase 1 checks, even when Check A already found a bar.

## 8. What counts as a knockout

A `knocked_out` verdict needs one of two things.

**A. A computed bar.** `state.json → bar.us_status` is `likely_barred` (from `state.py`), and the user has not reported an earlier filing that covers it.

**B. One verified reference that passes every test:**

- [ ] Every element is `explicit`, or `inherent` with evidence that it is necessarily there (MPEP 2112).
- [ ] The elements are arranged and connected the way the invention arranges them, in one embodiment or in a combination a skilled reader would at once envisage (MPEP 2131, 2131.02). Parts taken from unrelated embodiments do not count.
- [ ] `prior_art_basis` is `102(a)(1)` or `102(a)(2)`. Not `needs_evidence`, not `not_prior_art`.
- [ ] The reference is not the inventor's own disclosure inside the grace period (35 U.S.C. 102(b)(1)). Check intake.
- [ ] `verified: true`, and every element has a pinpoint and a quote that passes `quote_check.py`.
- [ ] The reference appears to enable what it shows. Prior art is presumed enabling (MPEP 2121), but flag an obviously speculative one-line mention.

An obvious pairing of two references is **not** a knockout. It makes the verdict 🟠 crowded, with the pair, the gap each fills, and a stated reason to combine (KSR rationale from `novelty-and-obviousness.md`).

## 9. False-knockout traps

A wrong knockout throws away a real invention. Run this list against every candidate before you call it.

| Trap | What it looks like | What to do |
|---|---|---|
| Genus vs species | The reference says "a fastener"; the element is "a magnetic clasp." | State `partial`. A genus rarely anticipates a species (MPEP 2131.02). The reverse is fine: a species in the reference does show a generic element. |
| Wrong arrangement | All the parts are there, but in a different place or relationship ("lights on the bike, not the helmet"). | State `partial` for the relationship. It may be a 103 secondary reference. |
| Mix-and-match embodiments | E1–E3 in FIG. 2, E4 only in an alternative in FIG. 7 that excludes FIG. 2's design. | Not anticipation unless one embodiment has all of them or the reader would at once envisage the combination. |
| Element only in a later family member | The element appears in a continuation-in-part, a later publication's amended claims, or added matter. The page shows the family's earliest priority date. | Date that disclosure by the document it first appears in. For 102(a)(2), the earlier application must itself describe it (35 U.S.C. 102(d)). |
| Undated web page or product | A product page, video, or repo with no provable date. | `needs_evidence`. Run `npl_fetch.py wayback`. Release notes, archive captures, and dated reviews can supply the date. |
| Inherency without evidence | "This chip probably has an accelerometer." | `unknown` until a datasheet or other evidence shows it is necessarily present. |
| Word match, different meaning | "Module" in the reference means a hardware board; in the invention it is a software routine. | Read the context. Mark `construction_dependent` and give both readings. |
| Long laundry list | The element is one item in a list of fifty options, combined with another list. | Usually not anticipation of the specific pairing unless the reader would at once envisage it. State `partial`. |
| Drawing-only disclosure | A figure seems to show the feature; the text is silent. | Drawings can anticipate if they clearly show the structure and how it fits (MPEP 2125). Proportions in drawings not stated to scale prove nothing. |
| Ranges | The reference gives a range that overlaps the inventor's. | Anticipation of ranges needs care (MPEP 2131.03). Usually `partial` plus a 103 note (MPEP 2144.05). |
| Post-cutoff document | Published after the cutoff, filed before it. | Only a US patent, US published application, or US-designating PCT publication can count as of its filing date (102(a)(2)). Foreign-only and NPL do not. |
| Machine translation | A CN or JP document read in Google's English. | Quote the translation, label it machine-translated, and mark the cell `[review]`. |
| Own grace-period disclosure | The closest "reference" is the inventor's own talk or post from eight months ago. | Not prior art under 102(b)(1)(A) if it came from the inventor. It is a bar-clock issue (`bars-and-eligibility.md`). |

## 10. Pivot suggestions (only for 🔴 or 🟠)

Offer pivots as questions, built only from the disclosure and the variants the user gave. Never invent a feature the user has not said they have.

Format, one row per pivot, at most three rows:

| Pivot (narrower or different feature) | Do you actually have it? | What the closest reference lacks for it | What to build or test to show it | Worth a deep search? |
|---|---|---|---|---|
| Auto-cancel of the signal from the rider's lean angle | ask | R1 [0021] cancels on a timer only | log lean angle vs cancel timing on 20 rides | yes, if it is what buyers pay for |

Rules:
- Each pivot must point to an element the closest reference marks `absent` or `partial`.
- Say what the claim would then rest on in one clause.
- If the user confirms a pivot, add it as a new element and re-run Check C with 3–5 targeted queries. Do not re-run logged queries.
