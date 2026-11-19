---
title: State files and data contracts
last_verified: 2026-11-18
sources:
  - internal contract for patentassist scripts and phases (no external source)
---

# State files and data contracts

Matter files live outside the installed skill/repository, by default `~/Desktop/PatentAssist/<matter>/`, or a user-chosen private directory. Pass `--dir` explicitly; legacy helpers default to `patent/` relative to their working directory. A new session reads `state.json` and current reviews to resume. Scripts read and write these files; the model reads them instead of re-asking.

Rules:
- Files are UTF-8. JSON is pretty-printed with 2-space indents and sorted top-level keys where order does not matter.
- Data documents carry a `schema` string (the review index is a simple phase-to-filename map). Scripts refuse a file whose major version they do not know.
- Dates are ISO `YYYY-MM-DD`. Timestamps are ISO 8601 UTC.
- Nothing in these files is ever sent to a third party by a script except the abstracted search queries the user approved (see SKILL.md confidentiality rule).

## Folder layout

```
patent/
  state.json                 matter state, phase verdicts, decisions, artifact hashes
  audit.jsonl                append-only log: queries, fetches, verifications, gates, checks, exports
  invention-disclosure.md    the invention, fixed headings (templates/invention-disclosure.md)
  prior-art.json             search log + references + element map (schema below)
  cache/                     fetched patent and NPL records (patentassist/patent@1), one file per number
  charts/                    claim charts (patentassist/chart@1)
  reports/                   lite-report.md, search-report.md, fto-screen.md, etc.
  reviews/                   numbered assessment records and index.json
  draft/
    support-map.md           limitations, disclosure/spec/figure support and provenance
    claims.md                claim set (format below)
    spec.md                  specification (format below)
    figures.json             figure plan (patentassist/figures@1)
    filing.json              ADS / cover-sheet data (patentassist/filing@1)
    out/                     built files: spec.docx, drawings.pdf, worksheets, fee sheet, manifest
  prosecution/
    oa-YYYY-MM-DD/           one folder per office action: oa.txt, inventory.json, response.md
  portfolio.json             docket register (patentassist/portfolio@1)
```

## state.json (`patentassist/state@1`)

```json
{
  "schema": "patentassist/state@1",
  "matter": {"title": "Helmet signal system", "created": "2026-11-18", "updated": "2026-11-18T20:00:00Z"},
  "profile": {
    "mode": "inventor",
    "role": "inventor",
    "reg_no": null,
    "customer_no": null,
    "confidentiality": "abstracted",
    "keys": {"uspto_odp": false, "epo_ops": false, "lens": false}
  },
  "phase": "lite",
  "phases": {
    "clarify": {"status": "done", "date": "2026-11-19", "report": null},
    "lite":  {"status": "done", "verdict": "no_knockout", "date": "2026-11-18", "report": "reports/lite-report.md"},
    "deep":  {"status": "not_started", "purpose": null, "outlook": null, "date": null, "report": null},
    "draft": {"status": "not_started", "filing_type": null, "claims_locked": false, "figures_locked": false, "date": null}
  },
  "dates": {
    "conception": null,
    "earliest_public_disclosure": null,
    "earliest_sale_or_offer": null,
    "earliest_public_use": null,
    "provisional_filed": null,
    "provisional_app_no": null,
    "nonprovisional_filed": null,
    "target_filing": null,
    "disclosures_confirmed": "none"
  },
  "bar": {"us_status": "clear", "us_last_day": null, "foreign_status": "intact", "computed": "2026-11-18"},
  "artifacts": {"invention-disclosure.md": {"sha256": "…", "updated": "…"}},
  "depends": {
    "draft/claims.md": ["invention-disclosure.md", "prior-art.json"],
    "draft/spec.md": ["draft/claims.md", "draft/figures.json"],
    "draft/out/": ["draft/spec.md", "draft/claims.md", "draft/figures.json", "draft/filing.json"]
  },
  "decisions": [{"date": "2026-11-18", "gate": "lite", "choice": "run deep search", "by": "user"}],
  "open_questions": ["Inventor 2 mailing address"]
}
```

Allowed values:
- `profile.mode`: `inventor` | `practitioner`. `profile.role`: `inventor` | `attorney` | `agent` | `paralegal` | `other`.
- `profile.confidentiality`: `abstracted` (default: queries use generic terms only) | `detailed` (user allowed specific technical terms in web queries).
- `phase`: `setup` | `clarify` | `lite` | `deep` | `draft` | `filed` | `prosecution`.
- `phases.*.status`: `not_started` | `in_progress` | `done` | `skipped`.
- `phases.lite.verdict`: `knocked_out` | `crowded` | `no_knockout`.
- `phases.deep.purpose`: `patentability` | `fto` | `invalidity` | `landscape`. `phases.deep.outlook`: free text scoped assessment; favorable and adverse conclusions are permitted when justified.
- `phases.draft.filing_type`: `provisional` | `nonprovisional` | `nonprovisional_claiming_priority`.
- `bar.us_status`: `clear` | `clock_running` | `likely_barred` | `unknown`. `bar.foreign_status`: `intact` | `at_risk` | `likely_lost` | `unknown`.
- `dates.disclosures_confirmed`: `null` (bar questions not asked yet) | `"none"` (asked: no public disclosure, sale, offer, or public use) | `"yes"` (there was one; record its date). The bar stays `unknown` until this is `"none"` or a disclosure/sale/offer/use date is set, and `state.py show` keeps asking the bar questions while it is `null`.
- `decisions[].gate` (canonical gate ids; `state.py decide` refuses others unless `--force-gate`): `clarify` (confirmed invention) | `scope` (version-specific scope choice) | `lite` (lite→deep) | `deep` (deep→draft) | `claims` (legacy claim checkpoint) | `package` (filing package export) | `oa-strategy` (office-action response strategy) | `oa-final` (response sign-off) | `mine`.

**Staleness.** `artifacts` holds the sha256 of each file when it was last used downstream. `scripts/state.py stale` recomputes hashes and lists every downstream file whose inputs changed (for example, claims edited after the spec was written). Stale outputs must be rebuilt before export. `draft/filing.json` is hashed without its computed fields (`total_fee`, `spec_pages`, `drawing_sheets`; canonical JSON with sorted keys), so writing those back does not make `draft/out/` stale.

## audit.jsonl

One JSON object per line, never rewritten:
```json
{"ts": "2026-11-18T20:01:02Z", "kind": "query", "source": "google_patents_web", "query": "helmet turn signal wireless handlebar", "hits": 14, "phase": "lite"}
{"ts": "…", "kind": "fetch", "number": "US9457709B2", "source": "google_patents", "ok": true}
{"ts": "…", "kind": "verify", "ref": "R1", "result": "verified", "how": "google_patents title+date+assignee"}
{"ts": "…", "kind": "gate", "gate": "lite", "choice": "run deep search"}
{"ts": "…", "kind": "check", "script": "check_claims.py", "blocking": 0, "warnings": 3}
{"ts": "…", "kind": "export", "path": "draft/out/spec.docx", "sha256": "…"}
```
Kinds: `query`, `fetch`, `verify`, `quote`, `gate`, `check`, `export`, `note`.

## prior-art.json (`patentassist/prior-art@1`)

```json
{
  "schema": "patentassist/prior-art@1",
  "purpose": "patentability",
  "stage": "lite",
  "cutoff_date": "2026-11-18",
  "cutoff_basis": "no disclosure yet; today's date used as the effective filing date",
  "elements": [
    {"id": "E1", "text": "a helmet shell", "essential": true, "test": "a rigid shell worn on the head"},
    {"id": "E2", "text": "rear turn-signal lights on the shell", "essential": true}
  ],
  "vocabulary": {
    "E2": {"terms": ["turn signal", "indicator", "blinker", "directional light"], "confirmed_by_user": true}
  },
  "queries": [
    {"id": "Q1", "status": "run", "source": "google_patents_web", "query": "helmet \"turn signal\" handlebar wireless", "date": "2026-11-18", "hits": 14, "screened": 10, "elements": ["E2", "E3"], "summary_untrusted": true},
    {"id": "Q2", "status": "planned", "source": "websearch", "query": "site:patents.google.com helmet indicator", "planned": "2026-11-18", "elements": ["E2"]}
  ],
  "references": [
    {
      "id": "R1",
      "type": "patent",
      "number": "US9457709B2",
      "family": ["US20160144773A1"],
      "country": "US",
      "kind": "B2",
      "title": "Bicycle helmet with an adaptive light notification system that varies brightness",
      "assignee_or_authors": "…",
      "priority_date": "2014-11-26",
      "filing_date": "…",
      "pub_date": "2016-05-26",
      "grant_date": "2016-10-04",
      "url": "https://patents.google.com/patent/US9457709B2/en",
      "prior_art_basis": "102(a)(1)",
      "verified": true,
      "verified_how": "google_patents: number+kind+title+dates+assignee",
      "verified_on": "2026-11-18",
      "category": "X",
      "element_map": {
        "E1": {"state": "explicit", "pinpoint": "[0018]", "quote": "exact words copied from the fetched text"},
        "E2": {"state": "partial", "pinpoint": "[0021]", "quote": "…", "note": "lights are not said to be LEDs"},
        "E3": {"state": "absent", "pinpoint": null, "quote": null}
      },
      "notes": "closest single reference"
    }
  ],
  "read_not_cited": [{"number": "US8803674B2", "why": "lights on the bicycle, not the helmet"}],
  "combinations": [{"refs": ["R1", "R3"], "covers": ["E1", "E2", "E3", "E4"], "rationale": "KSR (G): known technique to improve similar device", "strength": "strong"}],
  "not_searched": ["non-English full text", "paid databases", "product manuals before 2010"]
}
```

Rules:
- `elements[].test` (optional): the element restated as a structural or functional test with no purpose words (not "a *pre-boil-over* signature" but "the dominant band shifts and the total level rises above a limit, held for N intervals"). Chart against the test; keep the purpose in `text` or a note.
- `vocabulary` (optional): per element, the synonym family shown to the user before searching, `{terms: [...], confirmed_by_user: bool}`.
- `queries[].status`: `planned` (written before running; no `hits`, has `planned` date) | `run` (missing `status` means `run`). A run may carry `ran_as` (the text that actually ran, when it differs from `query`), `tool_rewrote: true` (the search tool said it changed the query), and `summary_untrusted` (default `true`: candidate numbers come only from result titles and URLs). `search_log.py coverage` counts only run queries.
- `scripts/prior_art.py` writes elements, cutoff, vocabulary, reference stubs, element_map cells (state validated), combinations, read_not_cited, and not_searched; `verify_refs.py` fills each stub's metadata.
- `type`: `patent` | `application` | `npl` | `product` | `web`.
- `category` (EPO/PCT search-report convention): `X` = alone defeats novelty or makes obvious; `Y` = obvious when combined with another Y; `A` = background; `P` = published between priority and filing (intermediate); `E` = earlier-filed, published later (102(a)(2)-type).
- `element_map[*].state`: `explicit` | `inherent` | `partial` | `absent` | `unknown`. `unknown` (could not read enough) never collapses into `absent`. Add `"construction_dependent": true` when the match turns on how a term is read.
- Every `quote` must be a verbatim substring of the cached text for that reference. `scripts/quote_check.py` enforces this and rewrites `pinpoint` from the cache when it can.
- A reference with `verified: false` is labeled `UNVERIFIED` in every report, never goes on an IDS list, and never supports a `knocked_out` verdict.
- `prior_art_basis`: `102(a)(1)` | `102(a)(2)` | `not_prior_art` | `needs_evidence`. Computed by `verify_refs.py` from dates vs `cutoff_date`.

## Cached record (`patentassist/patent@1`) — `cache/<NUMBER>.json`

Written by `scripts/patent_fetch.py`. The model never edits cache files.
```json
{
  "schema": "patentassist/patent@1",
  "number": "US9457709B2", "country": "US", "kind": "B2", "doc_type": "patent",
  "title": "…", "abstract": "…",
  "assignees": ["…"], "inventors": ["…"],
  "priority_date": "…", "filing_date": "…", "publication_date": "…", "grant_date": "…",
  "application_number": "US14/552,936",
  "family": ["US20160144773A1"],
  "cpc": ["A42B3/0453"],
  "claims": [{"num": 1, "text": "1. A helmet comprising …", "depends_on": [], "independent": true}],
  "similar": [{"number": "US20160144773A1", "title": "…", "date": "2016-05-26"}],
  "description": [{"pid": "p0018", "label": "[0018]", "text": "…"}],
  "citations": {"backward": [{"number": "…", "examiner": true, "date": "…"}], "forward": [{"number": "…", "examiner": false, "date": "…"}]},
  "legal_status": "Expired - Fee Related", "expiration": "…",
  "source": "google_patents", "url": "…", "fetched": "2026-11-18T20:01:02Z"
}
```
A claim whose text only says it was deleted or canceled (any wording Google shows, e.g. "delete") has `"canceled": true` and `"independent": false`. `similar` is Google Patents' "Similar Documents" list (`patent_fetch.py similar NUMBER` prints it).
NPL records use the same file with `doc_type: "npl"`, `doi`, `authors`, `venue`, `pub_date`, and `text` or `abstract` (with `abstract_source`: `crossref` or `openalex`).

## Claim chart (`patentassist/chart@1`) — `charts/<name>.json`

```json
{
  "schema": "patentassist/chart@1",
  "kind": "patentability",
  "subject": {"type": "invention", "label": "Helmet signal system", "claim": null},
  "elements": [{"id": "1a", "text": "A helmet comprising a shell;", "construction_note": null}],
  "refs": [{"id": "R1", "number": "US9457709B2"}],
  "cells": [
    {"element": "1a", "ref": "R1", "state": "explicit", "construction_dependent": false,
     "quote": "…", "pinpoint": "[0018]", "analysis": "…", "verified": false}
  ],
  "needs_evidence": ["1c vs R2: accelerometer implied only by a part number"]
}
```
- `kind`: `patentability` | `invalidity` | `infringement` | `fto`.
- Patentability and invalidity cells use the five states above. Infringement and FTO cells use `literal` | `doe` | `partial` | `absent` | `unknown`, with `construction_dependent` as a flag.
- `verified` starts `false`. A person ticks it after checking the cell against the source. Charts are leads, not contentions.
- `scripts/chart.py` renders Markdown, CSV (formula characters neutralized), and DOCX.

## Claims file — `draft/claims.md`

```
# Claims

1. A helmet comprising:
   a shell;
   a first light mounted on a rear portion of the shell; and
   a controller configured to …

2. The helmet of claim 1, wherein the first light comprises a light-emitting diode.
```
One claim per numbered paragraph. A claim may wrap lines; the number at line start begins a new claim. `scripts/check_claims.py` parses this format (and also accepts plain text with the same numbering).

## Specification — `draft/spec.md`

Markdown with these H2 headings in this order (37 CFR 1.77(b)); omit a heading only when its section does not apply:
`## TITLE` (one line under it) · `## CROSS-REFERENCE TO RELATED APPLICATIONS` · `## STATEMENT REGARDING FEDERALLY SPONSORED RESEARCH OR DEVELOPMENT` · `## THE NAMES OF THE PARTIES TO A JOINT RESEARCH AGREEMENT` · `## INCORPORATION BY REFERENCE OF THE SEQUENCE LISTING` (or computer program listing / table appendix, when submitted electronically) · `## STATEMENT REGARDING PRIOR DISCLOSURES BY THE INVENTOR OR A JOINT INVENTOR` · `## BACKGROUND` · `## SUMMARY` · `## BRIEF DESCRIPTION OF THE DRAWINGS` · `## DETAILED DESCRIPTION` · `## CLAIMS` (or a pointer to claims.md) · `## ABSTRACT`.
Paragraphs are plain text; `build_docx.py` numbers them `[0001]`, `[0002]` … Reference numerals appear as bare numbers after the element name (`shell 102`). Figures are cited as `FIG. 1`, `FIGS. 2A-2C`.

## Figure plan (`patentassist/figures@1`) — `draft/figures.json`

```json
{
  "schema": "patentassist/figures@1",
  "sheet": "letter",
  "figures": [
    {"id": "FIG. 1", "type": "block", "title": "system overview",
     "nodes": [{"id": "n1", "label": "Helmet", "numeral": 100}, {"id": "n2", "label": "Controller", "numeral": 110, "parent": "n1"}],
     "edges": [{"from": "n2", "to": "n3", "label": "wireless link"}]},
    {"id": "FIG. 2", "type": "flowchart", "title": "method",
     "steps": [{"numeral": 202, "label": "Receive button press"}, {"numeral": 204, "label": "Decision: left or right?", "kind": "decision", "yes": 206, "no": 208}]}
  ]
}
```
Types generated in v1: `flowchart`, `block`, `sequence`, `wireframe`, `graph`, `image` (user-supplied line art placed on a sheet with numerals added). Each numeral means exactly one element across all figures and the spec.

Every key `scripts/drawings.py` reads is listed below with its default. Any other key gets a WARN `unknown-key` at build time, because a misspelled key is otherwise silently ignored. Keys that start with `_` are comments and are ignored.

**Top level**

| Key | Default | Meaning |
|---|---|---|
| `schema` | required | `"patentassist/figures@1"` |
| `sheet` | `"letter"` | `"letter"` (21.6 x 27.9 cm) or `"a4"` (21.0 x 29.7 cm), 37 CFR 1.84(f) |
| `text_case` | `"upper"` | `"upper"` capitalizes labels so every letter meets 0.32 cm (text in parentheses, such as units, is left alone); any other value keeps labels as typed |
| `figures` | required | list of figures, in FIG. order |

**Every figure**

| Key | Default | Meaning |
|---|---|---|
| `id` | required | `"FIG. 1"`; partial views `"FIG. 3A"`, `"FIG. 3B"`. Unique |
| `type` | required | `flowchart`, `block`, `sequence`, `wireframe`, `graph`, `image` |
| `title` | `""` | short name, kept in the manifest |
| `text_case` | top-level value | per-figure override |
| `own_sheet` | `false` | put this figure alone on a sheet |
| `new_sheet` | `false` | start a new sheet before this figure |

**`flowchart`**: `steps[]`, drawn top to bottom. A flowchart that does not fit is redrawn in a compact style first.

| Step key | Default | Meaning |
|---|---|---|
| `numeral` | none | reference numeral (connectors usually have none) |
| `label` | `""` | text in the box; for a connector, its letter |
| `kind` | `"step"` | `step` (also `process`, `io`, `action`): rectangle. `start`, `end`: rounded box. `terminal` / `terminator`: `start` if first, else `end`. `decision`: diamond. `connector` (also `off-page`): off-page connector, the letter in a circle |
| `next` | `"next"` | the following step; or a step numeral, a connector letter, or `null` for no outgoing line |
| `next_label` | `""` | text beside the outgoing line |
| `yes`, `no` | none | decision targets: a step numeral or a connector letter |
| `yes_label`, `no_label` | `"YES"`, `"NO"` | branch text |

Split a long flowchart into partial views with connectors: FIG. 3A ends with `{"kind": "connector", "label": "A"}` (a decision branch may point at `"A"`), and FIG. 3B starts with the same connector. Each connector letter must appear in at least two views (WARN `connector-unpaired`). `drawings.py build` prints a size budget per figure: the scale it needs, the smallest scale 0.32 cm text allows, and about how many steps or boxes fit in one view (about 9 to 11 flowchart steps, about 10 block boxes).

**`block`**: layered boxes and connectors.

| Key | Default | Meaning |
|---|---|---|
| `direction` | `"TB"` | `"TB"` top to bottom, or `"LR"` (also `RL`, `H`, `horizontal`) left to right. If the requested direction does not fit at 0.32 cm text, the other one is tried; if neither fits, the larger-scale layout is kept and the build says so |
| `nodes[]` | required | `{id, label, numeral, parent, style}`: `id` required and unique; `parent` is the `id` of the enclosing box (a node named as a parent is drawn as a container); `style` `"solid"` (default) or `"dashed"` |
| `edges[]` | `[]` | `{from, to, label, arrow, style}`: node ids; `label` `""`; `arrow` `"forward"` (default), `"backward"`, `"both"`, `"none"`; `style` `"solid"` or `"dashed"`. An edge is routed around every box that is not one of its ends; its label sits beside the longest run of the line inside one container |

**`sequence`**: `participants[]` (alias `lifelines`) `{id, label, numeral}`; `messages[]` `{from, to, label, numeral, kind}`, in time order. `from` equal to `to` draws a self-message. `kind` `"call"` (default) is solid; `return`, `reply`, `response`, `async_return` are dashed.

**`wireframe`**: `device` is a kind string or `{kind, width_pt, height_pt, numeral, label}`. `kind` is `phone` (default, 200 x 400 pt), `tablet` (300 x 410), `browser` or `desktop` (400 x 290), `watch` (160 x 190), or `screen` (360 x 260); `label` defaults to the kind. `regions[]` are `{x, y, w, h, shape, label, numeral}`, with `x`, `y`, `w`, `h` as fractions of the screen (defaults 0, 0, 0.2, 0.1). `shape` is `rect` (default), `circle`, `button`, `image`, or `text`.

**`graph`**: `kind` (alias `chart`) `"line"` (default) or `"bar"`; `width_pt` 300 and `height_pt` 210 (the plot area); `x_label`, `y_label` `""`; `series[]` `{label, numeral, points: [[x, y], ...]}`; `bars[]` `{label, value, numeral}` (a bar chart without `bars` uses the first series' points).

**`image`**: `path` (alias `src`, required, relative to the figures.json folder); `threshold` 160 (0 to 255 cut for the black and white conversion; needs Pillow); `max_width_pt` 360 and `max_height_pt` 470; `numerals[]` (alias `callouts`) `{numeral, label, x, y}`, with `x`, `y` as fractions of the image (0 to 1). `x` below 0.5 puts the numeral in the left column.

The build writes `draft/out/drawings-manifest.json` (`patentassist/drawings-manifest@1`). Per figure it records the sheet, scale, bounding box, numerals with their text boxes (`text_bbox_pt`), and, for block diagrams and flowcharts, `nodes[]` (`box_pt`, `parent`, `container`), `edges[]` (`pts_pt` polylines), and `edge_labels[]`, all in page points from the top-left. `check_drawings.py` uses that geometry for `EDGE_CROSSES_NODE` (BLOCK) and `EDGE_CROSSES_NUMERAL` (WARN).

## Filing data (`patentassist/filing@1`) — `draft/filing.json`

ADS / cover-sheet facts. Every value comes from the user; `null` = not given yet (shown as `[ask user]` in worksheets); `false` = no. Scripts never guess. Field names (authoritative list in `scripts/fill_forms.py` docstring):

```
filing_type            provisional | nonprovisional | nonprovisional_claiming_priority
title, attorney_docket, application_number, filing_date, art_unit, examiner
inventors[]            {prefix, given, middle, family, suffix,
                        residence: {city, state, country, military},
                        mailing: {address1, address2, city, state, postcode, country}, email, phone}
applicants[]           empty = inventors are the applicant; else {kind: assignee | obligated_assignee |
                        proprietary_interest | legal_representative | joint_inventor,
                        org_name | {given, middle, family}, address, email, phone}
assignees[]            non-applicant assignees to print on the publication
correspondence         {customer_no} or {name, name2, address, email, phone, fax}
entity_status          large | small | micro ; micro_basis: gross_income | higher_education
domestic_benefit[]     {prior_app_no, prior_filing_date, relationship, status, patent_number, issue_date}
foreign_priority[]     {app_no, country, filing_date, access_code}
government_interest    {funded, made_by_agency, agency, contract_no}
representative         {customer_no, practitioners: [{given, family, reg_no}]}
nonpublication_request, early_publication, pdx_opt_out, epo_search_opt_out, secrecy_order   (bools)
ads_enclosed, drawing_sheets, spec_pages, suggested_figure, other_enclosures, total_fee
signer                 {given, middle, family, reg_no, phone, title}   typed name only, never a signature
```

## Portfolio (`patentassist/portfolio@1`) — `portfolio.json`

```json
{"schema": "patentassist/portfolio@1", "assets": [
  {"id": "A1", "title": "…", "jurisdiction": "US", "type": "utility", "status": "pending",
   "app_no": "…", "patent_no": null, "filing_date": "…", "priority_date": "…", "grant_date": null,
   "entity": "small", "events": [{"type": "office_action", "date": "…", "mailed": "…"}]}
]}
```
`scripts/deadlines.py portfolio` computes `next_deadlines` from events (never trusts stored deadline dates) and groups them: overdue-in-grace, due ≤30 days, due ≤90 days, later, unknown.

## Versioned reviews (`patentassist/review@1`)

Complete `templates/assessment.json` in the private matter. `review.py record --phase PHASE --input FILE --dir MATTER` validates it and writes a new numbered file under `reviews/`; `index.json` identifies the latest record for each phase. `review.py check` validates required fields and compares input hashes. Prior records are not overwritten by the tool.

Phases: `clarify`, `lite`, `deep`, `draft`. All require scope, bottom_line, examiner_objection, applicant_response, resolution, next_action, uncertainty, inventor_fidelity, scope_confirmed, coverage, grounds and reference_ids. `coverage.search` is none/limited/substantial; `coverage.limits` must describe remaining limitations. This records actual review, not a checkbox substitute for it.

Clarify outcomes: ready_to_search / needs_clarification / eligibility_concern / disclosure_concern / bar_concern. No prior-art assessment in Phase 0. Lite: likely_unpatentable / no_blocker_found / inconclusive. Deep/draft: likely_patentable / likely_unpatentable / inconclusive. Other deep purposes use assessed_risks / inconclusive. A favorable patentability finding requires substantial recorded search/review and confirmed scope. Prior-art grounds require referenced IDs with recorded source verification.

Draft reviews require confirmed scope and hash disclosure, prior-art.json, claims, spec, figures, filing data and support-map.md. An adverse/inconclusive draft also requires `proceed_basis`, recording the user's real instruction to continue despite those limits. Computed filing totals/page counts are excluded. All phases hash their relevant current inputs; a material edit needs a new review. The checker validates structure, flags and freshness, not legal truth, source accuracy or actual human confirmation.

Legacy claims_locked/figures_locked fields remain readable as checkpoint markers. They are not permanent locks or proof of current review. `check_package.py` requires a current draft assessment and shows adverse/unresolved outcomes explicitly.
