# patentassist scripts

Deterministic helpers. The model reasons; these scripts fetch, verify, count, check, and build. Every script is also written so it can later be exposed as a tool by a host app: a pure `run(args) -> dict` function plus a thin CLI.

## Conventions (all scripts)

- **Python 3.9+**, standard library first. Optional libraries, imported lazily with a clear install hint if missing: `python-docx` (DOCX), `pypdf` (PDF forms, reading PDFs), `reportlab` (drawing sheets), `lxml`/`bs4` are NOT required (parse HTML with `html.parser`).
- Run as `python3 scripts/<name>.py <command> [options]`. Every script has `--help`, `--dir` (default `patent`), and `--json` (machine-readable output on stdout).
- **Exit codes:** `0` ok / no blocking findings, `1` blocking findings, `2` usage or input error, `3` network or source failure.
- **Ran/skipped ledger.** Every checker prints which checks it ran and which it skipped (with the reason). A report may say "no blocking issues" only when every required check ran.
- **Findings format** (text mode): `BLOCK|WARN|INFO  <code>  <location>  <message>`; JSON mode: `{"findings": [{"level", "code", "where", "message"}], "checks_run": [...], "checks_skipped": [{"check", "reason"}], "summary": {...}}`.
- **Audit.** Scripts that query, fetch, verify, check, or export append one line to `<dir>/audit.jsonl` (see references/state-files.md) unless `--no-audit`.
- **Network.** Only `patent_fetch.py`, `verify_refs.py`, `npl_fetch.py`, and `colline.py fetch` touch the network. They send a generic User-Agent (`patentassist/1.0 (+https://github.com/)`), never user data beyond the document number or approved query, sleep ≥1 s between requests to one host, retry twice with backoff, and cache every response under `<dir>/cache/`. `--offline` uses cache only.
- **Tests** live in `tests/` (stdlib `unittest`, no network: fixtures in `tests/fixtures/`). Run `python3 -m unittest discover -s tests`.
- No secrets in files. API keys come from env vars: `USPTO_ODP_API_KEY`, `EPO_OPS_KEY` + `EPO_OPS_SECRET`, `LENS_TOKEN`.

## Scripts

| Script | Job | Phase |
|---|---|---|
| `state.py` | init / show / set / log decisions / stale-check artifacts / next-gate hint | all |
| `prior_art.py` | edit prior-art.json safely: elements (with purpose-free `test`), cutoff, vocabulary, references, cells (validated states), combinations, read-not-cited, not-searched | search |
| `normalize_number.py` | parse any patent, publication, or application number into canonical forms + URLs | all |
| `patent_fetch.py` | fetch a patent or publication (Google Patents HTML → ODP/EPO if keys) into `cache/` as `patentassist/patent@1`; `similar NUMBER` lists Google's similar documents (keyless fallback when web search is down) | search, analyze |
| `npl_fetch.py` | fetch NPL metadata (Crossref → OpenAlex → arXiv) and earliest Wayback capture for web pages | search |
| `verify_refs.py` | verify every reference in `prior-art.json` against fetched records; family de-dupe; prior-art basis vs cutoff | search, draft |
| `quote_check.py` | confirm every quote in prior-art.json / charts is verbatim in the cached text; fill pinpoints | search, analyze |
| `manifest.py` | write draft/out/manifest.md + .json: each file, sha256, size, Patent Center document description, required/optional by filing type; logs the export | draft |
| `_specparse.py` | shared spec parsing (sections, FIG. references, numerals) used by check_spec and check_drawings | internal |
| `colline.py` | US grants: download the PDF and turn a quote into a `col. 4, ll. 10-22` pinpoint (PyMuPDF); `annotate` fills `pinpoint_colline` in prior-art.json / charts | search, analyze |
| `search_log.py` | `plan` queries before running, `add --id` results (`--ran-as`, `--tool-rewrote`), list, coverage (planned vs run), re-run diff | search |
| `chart.py` | render a chart JSON to Markdown / CSV / DOCX; validate states; list needs-evidence | search, analyze |
| `ids.py` | build IDS data (PTO/SB/08 sections) from verified references; IDS size-fee tier | draft, prosecution |
| `check_claims.py` | parse claims; dependency tree; antecedent basis; 112(f) and indefinite-term flags; fee counts; term support in spec | draft, prosecution |
| `check_spec.py` | section order; title/abstract limits; FIG. coverage; numeral consistency; risky words; funding statement | draft |
| `check_package.py` | whole-package consistency before export; stale inputs; leftover notes; blocker list | draft |
| `fees.py` | fee estimate by entity status, filing type, claim counts, page count, IDS size, extensions | draft, prosecution |
| `deadlines.py` | deadline math with weekend/holiday roll; bar-date clock; portfolio docket | all |
| `build_docx.py` | spec.md + claims.md → Patent Center–ready DOCX | draft |
| `drawings.py` | figures.json → SVG + 37 CFR 1.84 PDF sheets (flowchart, block, sequence, wireframe, graph, image) | draft |
| `check_drawings.py` | numerals in figures ⇄ spec both ways; FIG. list ⇄ Brief Description; sheet rules | draft |
| `fill_forms.py` | fill AcroForm USPTO PDFs where possible; otherwise write a field-by-field worksheet | draft |
| `oa_parse.py` | office action text → inventory.json (rejections, claims, statutes, references, objections) | prosecution |
| `oa_check.py` | response completeness; 37 CFR 1.121 amendment markup; no-new-matter word check | prosecution |
| `md_to_docx.py` | generic Markdown → DOCX for reports and memos | all |

## Assessment history and public-release checks

`review.py record --phase clarify|lite|deep|draft --input FILE --dir MATTER` saves a new numbered assessment. Complete the assessment template with actual scope, objection, response, resolution, coverage, uncertainty, provenance and next action. `review.py check --phase PHASE --dir MATTER` checks fields, source-verification flags and current-input hashes. Draft reviews require `draft/support-map.md`; an inconclusive/adverse draft requires the user's actual `proceed_basis`. No helper verifies legal truth or human approval.

`check_package.py` requires a current draft review. Old `claims_locked`/`figures_locked` fields are compatibility checkpoint markers only. Material revisions require new substantive review.

`check_release.py` checks the source tree for unexpected files, common secret/private-path patterns, required entry points and broken local Markdown links. It is a release aid, not a comprehensive privacy proof. Review actual staged files before publishing; never run a real matter inside this repository.
