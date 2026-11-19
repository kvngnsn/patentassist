---
title: 'Deep search methodology (Phase 2: patentability, FTO, invalidity, landscape)'
last_verified: 2026-11-18
sources:
  - url: https://www.law.cornell.edu/uscode/text/35/122
    supports: 35 U.S.C. 122(b) publication at 18 months; provisional applications are not published; nonpublication requests.
  - url: https://www.law.cornell.edu/uscode/text/35/154
    supports: 35 U.S.C. 154(a)(2) term (20 years from the earliest US nonprovisional filing relied on under 120/121/365(c)/386(c)), 154(a)(3) foreign and provisional priority not counted, 154(b) term adjustment, 154(d) provisional rights.
  - url: https://www.law.cornell.edu/uscode/text/35/311
    supports: 35 U.S.C. 311(b) IPR grounds limited to 102 and 103 on patents and printed publications.
  - url: https://www.law.cornell.edu/uscode/text/35/321
    supports: 35 U.S.C. 321(b)-(c) PGR on any invalidity ground, petition within 9 months of grant.
  - url: https://www.law.cornell.edu/uscode/text/35/301
    supports: 35 U.S.C. 301-302 ex parte reexamination based on patents and printed publications.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2128.html
    supports: MPEP 2128-2128.02 printed publications and public accessibility (theses, online material, dates).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2152.html
    supports: MPEP 2152.01 effective filing date per claim; grace-period weekend rule (35 U.S.C. 21(b)).
  - url: https://www.fcc.gov/engineering-technology/laboratory-division/general/equipment-authorization
    supports: FCC equipment authorization (FCC ID grants are public). FCC short-term confidentiality guidance (KDB 726920) lets manuals, photos and schematics stay confidential for a limited time after grant; each exhibit's public-release date appears in the exhibit list. fcc.gov blocks scripted fetches; the user may need to open it in a browser.
  - url: references/sources-and-apis.md
    supports: Every source, key, quota, and the Wayback dating rule used here.
  - url: references/state-files.md
    supports: prior-art.json, chart, and audit.jsonl contracts; X/Y/A/P/E categories.
---

# Deep search methodology

Load this at Phase 2, Step 2. It covers how to search. What the results mean legally is in `novelty-and-obviousness.md`, `case-law/anticipation.md`, `case-law/obviousness.md`, and `case-law/infringement.md`. Endpoints, keys, and quotas are in `sources-and-apis.md`.

Rule zero: search like an examiner. Screen widely, read closely, and log everything so the search can be replayed.

## 1. Element to vocabulary family

Build one family per element `E1..En` (or claim element `1a, 1b…` in invalidity mode). Show all families to the user in one compact table.

| Slot | Meaning | Example for "rear turn-signal light on a helmet" |
|---|---|---|
| Core terms | the inventor's words | turn signal, helmet |
| Synonyms | same thing, other words | direction indicator, blinker, indicator lamp |
| Broader | genus | signaling device, light source, visual indicator |
| Narrower | species | LED strip, light guide, OLED panel |
| Functional | what it does | indicate direction of travel, alert following traffic |
| Legacy names | older or trade words | trafficator, winker (common in translated Japanese text) |
| Cross-field analogues | the same idea elsewhere | cyclist backpack signal, glove signal, vehicle mirror indicator |
| Non-English | terms for NPL and original-language text | Blinker (DE), clignotant (FR), 方向指示 (JA), 转向灯 (ZH) |
| Misspellings and variants | hyphenation, plurals, US/UK | turn-signal, colour, aluminium |

Rules:
- Add terms from the closest fetched references. Their claim words are the field's real vocabulary.
- Machine translations on Google Patents use odd English. Add the translation's words once you see them.
- Keep the family to about 8–15 terms. More terms means noisier OR groups.

### Adjacent-families sweep (confirm with the user)

Before running the plan, show the families and ask once:

> "Here is the vocabulary I'll search for each part. Add any words your field uses, older product names, or competitor names. Remove anything that is wrong."

Record the user's additions as `source: user` in the plan. Report coverage per family at the end, so a reader can see which wording was searched.

## 2. CPC-driven search

Details and a starter table are in `cpc-primer.md`.

1. Count the CPC codes in `cache/*.json → cpc` across the top 5 fetched references. The codes that repeat are the field's home.
2. Confirm each code's meaning on the official scheme page before using it.
3. Pick 2–4 groups. Go up one level (fewer dots) if a group gives few hits. Go down one level if it floods.
4. Combine one code string with one or two keywords: `site:patents.google.com "G06N3/08" "battery swap"`.
5. For older or foreign art, the IPC symbol usually matches the CPC main group. Use the main group if a fine CPC subgroup returns nothing.
6. Note CPC warnings on the scheme page ("impacted by reclassification"). Search both the old and new groups named in the warning.

## 3. Assignee and inventor searches

Players are found from the closest references, the user's competitor list, and landscape results.

- List the top 3–5 assignees and the 3–5 most frequent inventors among relevant hits.
- Query each with one or two element terms: `site:patents.google.com "Acme Robotics" gripper "vacuum cup"`.
- Try name variants: Inc/Corp/LLC/GmbH/Co Ltd, former names, parent and subsidiary names, transliterations (Chinese and Korean assignees often appear several ways).
- Follow inventors across employers. Inventors keep working on the same idea after they change companies.
- With a `USPTO_ODP_API_KEY`, search ODP by applicant name for US filings. With EPO OPS keys, pull families for the best hits.

## 4. Non-patent literature (NPL)

Examiners cite NPL often in software, AI, biotech, and electronics. Plan at least two NPL query families at standard depth.

| Source | How | Dating and access notes |
|---|---|---|
| Papers (scholarly index) | `npl_fetch.py search "…"` (Crossref, then OpenAlex); `npl_fetch.py doi …` | Use the publication date in the record. Online-first dates can be earlier than the issue date. Google Scholar has no API; use available web search only to find leads. |
| Preprints | `npl_fetch.py arxiv <id>`; available web search `site:arxiv.org` | arXiv gives submission and version dates. Cite the version that contains the element. |
| Standards | available web search `site:ietf.org`, `site:3gpp.org`, `site:etsi.org`, `site:w3.org`; IEEE and ISO abstracts | Standards and drafts carry dates. Contributions and drafts are often public before the final standard. |
| Theses | available web search `thesis OR dissertation` + terms; university repositories | Public once cataloged or indexed so a diligent searcher could find it (MPEP 2128.01). Record the catalog date if you can. |
| Code | available web search `site:github.com`; package registries (PyPI, npm) | Commit dates can be set by the author. Prefer release tags, registry publish dates, and archive captures. |
| Product manuals and datasheets | manufacturer support pages; available web search `manual OR datasheet` | Version and print dates inside the PDF; confirm with Wayback. |
| Radio devices | FCC Equipment Authorization database (FCC ID) | Grant dates are public. Some exhibits stay confidential for a period; check the release date of the exhibit you rely on. |
| Videos and talks | conference sites, video platforms | Upload date plus the frame or timestamp that shows the element. |
| Any web page | `npl_fetch.py wayback URL` | Earliest 200 capture proves the page existed no later than then. No provable date: `needs_evidence`. |

## 5. Citation chasing

Run after the first round of reading.

- **Backward:** what the top references cite (`citations.backward`).
- **Forward:** what later cites them (`citations.forward`). Forward hits are often the closest art for an improvement.
- **Weighting:** examiner-cited first, then applicant-cited. In family members' records, EP and WO search-report citations marked X or Y are strong leads.
- **Family citations:** chase citations from every family member in `family`; different offices cite different art.
- **Depth:** one hop on the top 5 at standard depth; two hops (citations of citations) at thorough depth, screening titles only on the second hop unless a title looks close.
- Log each hop as a note in `audit.jsonl` with the seed reference and the number screened.

## 6. Depth defaults by mode

| Depth | Screened (pass 1) | Read (passes 2–3) | Citation hops | NPL | When |
|---|---|---|---|---|---|
| quick | about 40 | about 10 | 1 hop on top 3 | 1 family | cheap second look after Phase 1 |
| standard (default) | about 100 | about 25 | 1 hop on top 5 | 2+ families | normal patentability search, FTO screen |
| thorough | about 250 | about 50 | 2 hops on top 5 | all sources in Section 4 | invalidity, high-value filings, crowded fields |

Screen and read counts are targets, not quotas. Report the actual numbers. Never imply more coverage than you did.

## 7. Coverage matrix rule

- Every element must be searched in at least **two different source types** (Google Patents web, plain web, Crossref/OpenAlex, arXiv, ODP, EPO OPS). `search_log.py coverage` must show it before the report.
- A query counts for an element only if the plan listed that element for it.
- Essential elements should also have at least one CPC-anchored query and one NPL query.
- If an element cannot reach two sources (for example, no NPL exists for a mechanical latch), say so in the coverage block with the reason.

## 8. Recording what you read

- Every document that reached pass 2 is either cited in `references` or listed in `read_not_cited` with a one-line reason.
- Useful reasons: "same as R2 (family member)", "element E3 on the vehicle, not the helmet", "after cutoff, foreign-only", "no date", "different problem; no E1".
- Family members are one entry. `verify_refs.py` de-duplicates families; cite the best-dated member and list the rest under `family`.

## 9. Diff re-search

When a matter already has a search on file:

1. `python3 scripts/search_log.py rerun-plan --since YYYY-MM-DD` replays the saved queries.
2. Start the window about two months before the last run. Indexes lag, so late-indexed documents get caught.
3. Report only what is new: new documents, new family members, legal-status changes, and new claim versions of pending applications.
4. Good times to re-run: before converting a provisional (months 9–11), before filing an IDS, before launch for an FTO screen, and when a new competitor appears.

## 10. Stopping criteria

Stop the search when all of these are true:
- [ ] The depth target for the chosen mode is met, or the user's time cap is reached.
- [ ] The coverage rule (Section 7) is met or each gap is explained.
- [ ] Saturation: the last 5 queries surfaced no new document that would rank in the top 10.
- [ ] Citation chasing for the chosen depth is done.

Finding an X reference does not end a patentability search early. Finish the plan so the report can show the white space and the 103 picture.

## 11. Honest limitations (say these in every report)

- **The 18-month blind spot.** Applications are generally published 18 months after their earliest priority date (35 U.S.C. 122(b)). Anything filed in the last 18 months may exist and be invisible. Provisional applications are never published on their own.
- **Paid databases not searched.** Commercial patent databases and chemical-structure or sequence databases have coverage and search tools this skill does not. Free partial options exist (public sequence and compound databases) but are not a structure or sequence search of the patent literature.
- **Non-English full text.** Google's machine translations cover many CN, JP, KR, and DE documents, but older and NPL documents in other languages are often missed.
- **Paywalled NPL.** Abstracts are searchable; full text often is not.
- **Unindexed art.** Old catalogs, trade-show handouts, internal products, and anything only on paper.
- **Images.** Keyword search cannot find a feature shown only in a drawing.

## 12. FTO screen specifics

FTO asks whose in-force claims the product might practice. It is a different search from patentability.

**What to search**
- Use product features as elements, one row per feature that matters commercially.
- Target claim language. Search for how a claim would describe the feature, not how marketing does.
- Limit to documents that can be or become enforceable: granted patents not expired, plus pending published applications and their continuations.
- Search each country where the product is made, used, sold, offered, or imported, one at a time. A US patent does nothing in Germany.

**Status and expiry checks (per patent)**
- [ ] Granted or pending? A pending application has no enforceable claims yet, but its claims can still change and may issue. Note provisional rights under 35 U.S.C. 154(d).
- [ ] Expected expiry: 20 years from the earliest US nonprovisional filing date it relies on (35 U.S.C. 154(a)(2)). Provisional and foreign priority do not count toward term (154(a)(3)).
- [ ] Adjustments: term adjustment (154(b)), terminal disclaimers, and extensions for regulated products (35 U.S.C. 156).
- [ ] Maintenance fees paid? Unpaid fees end the patent early, but revival is possible. Fee timing is in `deadlines.md` and `fees.md`.
- [ ] Google Patents `legal_status` is a hint. Confirm in Patent Center, or with ODP if a key exists. If you cannot confirm status, say so. Never assume a patent has expired.
- [ ] Continuation family: list pending family members. New claims can be drafted to target the product.

**Charting and reporting** follow Phase 2's FTO section: one chart per independent claim, all-elements rule, doctrine of equivalents as a flag-only pass, a traffic light per patent and never a green for the whole screen. Keep the screen-not-opinion banner and the willfulness note (`report-format.md`).

## 13. Invalidity search specifics

**Before searching**
- [ ] Fetch the target and its family. Parse the asserted claims into elements `1a, 1b…` and show the parse.
- [ ] Set the cutoff per claim. The effective filing date can differ by claim when a later application added matter (continuation-in-part) or when an earlier provisional does not support a claim. Check what each priority document actually describes.
- [ ] Note whether pre-AIA or AIA 102 applies: claims with an effective filing date before March 16, 2013 use pre-AIA law (`novelty-and-obviousness.md`).
- [ ] Read the target's own record: the references it cites, and the examiner's reasons for allowance if the file wrapper is available (ODP key, or the user supplies it). The reasons for allowance say what the examiner thought was missing. Search for exactly that.
- [ ] Read foreign counterparts' search reports (EP, WO). X and Y citations there are strong leads.

**Art types and forums**

| Forum | Grounds allowed | Art that counts |
|---|---|---|
| IPR (35 U.S.C. 311(b)) | 102 and 103 only | patents and printed publications only |
| PGR (35 U.S.C. 321) | any invalidity ground, including 101 and 112 | any prior art; petition within 9 months of grant |
| Ex parte reexamination (35 U.S.C. 301-302) | substantial new question of patentability | patents and printed publications |
| District court | all defenses | everything, including products, public use, and on-sale activity |

- Prioritize printed publications and patents when the user is considering IPR.
- Products, demos, and sales go in a separate section for court use. Each needs dating evidence and proof of what was public.
- List the needs-evidence items first. They are the work plan.
- The burden in court is clear and convincing evidence; at the PTAB it is a preponderance. Say which forum each finding is aimed at.

## 14. Landscape mode

- Search broadly by CPC groups and vocabulary families; no element charts unless asked.
- Group by assignee, CPC, filing year, and theme. Report top assignees, filing trend, key families, patents expiring in the next 24 months, and white space.
- Offer a CSV. Neutralize cells that start with formula characters (`chart.py` does this).
