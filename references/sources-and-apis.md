---
title: patentassist data sources and APIs (verified)
last_verified: 2026-11-18
sources:
  - Google Patents (patents.google.com) - keyless, HTML + xhr/query
  - USPTO Open Data Portal (api.uspto.gov) - key required
  - PatentsView PatentSearch API (search.patentsview.org) - DEAD / paused
  - EPO Open Patent Services (ops.epo.org) - free registration, OAuth2
  - Lens.org API (api.lens.org) - token required
  - WIPO PATENTSCOPE - no open JSON API
  - USPTO Patent Public Search (ppubs.uspto.gov) - no documented public API
  - OpenAlex, Crossref, Semantic Scholar, arXiv - scholarly, keyless
  - Wayback Machine CDX / availability - keyless, dating web pages
---

# How to read this file

Every claim is tagged:
- **CONFIRMED-LIVE**: I got that response by curl on 2026-11-18.
- **CONFIRMED-DOC**: an official page says so (fetched or search-quoted).
- **UNVERIFIED**: third-party only, or I could not reach the doc. Treat as a hint; code must handle failure.

Historical connectivity observations below are dated snapshots, not a current availability guarantee. Recheck the documented source before relying on it.

# Keyless verification chain (for scripts)

1. **Google Patents HTML** `https://patents.google.com/patent/<NUMBER>/en` (keyless, works now).
2. If `USPTO_ODP_API_KEY` env set: **ODP** `applications/{appNo}/meta-data` (US only; authoritative for grant date, assignee, title).
3. If `EPO_OPS_KEY` + `EPO_OPS_SECRET` set: **EPO OPS** biblio (all countries; authoritative bibliographic data).
4. If `LENS_TOKEN` set: **Lens** patent search (cross-check, family).
5. Non-patent refs: Crossref (DOI) -> OpenAlex -> Semantic Scholar -> arXiv. Web pages: Wayback CDX for the earliest capture date.

A reference is VERIFIED only if number+kind exists AND title matches (normalized, fuzzy >= ~0.85) AND date matches AND assignee/applicant matches (normalized, "Co"/"Inc" stripped). Record which source confirmed it and what fetched. If only one keyless source answered, mark "verified (single source: Google Patents)".

---

# 1. Google Patents (keyless) - PRIMARY keyless verifier

**Covers**: US, EP, WO, CN, JP, KR, etc. Full text, claims, citations, dates, assignees.
**Auth**: none. **Limits**: undocumented; be polite (>=1 req/s, descriptive UA, back off on 429/captcha). **Terms**: `robots.txt` (CONFIRMED-LIVE) says `Disallow: /*` with `Allow: /$`, `/advanced$`, `/patent/`, `/sitemap/`. So `/patent/...` pages are allowed for crawlers; `/xhr/query` is NOT in the allow list (disallowed by robots.txt). Do NOT use `xhr/query` in the skill; it is an unofficial internal endpoint.

## Confirmed: patent page HTML
```
curl -A "Mozilla/5.0" https://patents.google.com/patent/US10000000B2/en
```
HTTP 200, ~277 KB, `text/html`. Server-rendered (no JS needed). Kind code may be omitted (`/patent/US10000000` -> 200). Nonexistent number -> 404 (CONFIRMED-LIVE with US99999999999B2). Also 200 for `US20230123456A1`, `WO2020123456A1`, `EP1000000A1`, `CN101234567A`.

Fields (CONFIRMED-LIVE on US10000000B2):
| Need | Where |
|---|---|
| Title | `<title>US10000000B2 - Coherent LADAR using intra-pixel quadrature detection - Google Patents</title>`; also `<span itemprop="title">` (first one; later ones are litigation rows, so take first) |
| Number (as granted) | `<meta name="citation_patent_number" content="US:10000000">`; `itemprop="publicationNumber"` first = `US10000000B2` (others are cited/family docs) |
| Application number | `<meta name="citation_patent_application_number" content="US:14/643,719">` |
| Filing date | `<meta name="DC.date" content="2015-03-10" scheme="dateSubmitted">`; `itemprop="filingDate" datetime=...` |
| Grant/issue date | `<meta name="DC.date" content="2018-06-19" scheme="issue">` |
| Priority date | `itemprop="priorityDate" datetime="2015-03-10"` |
| Inventors | `<meta name="DC.contributor" content="Joseph Marron" scheme="inventor">` |
| Assignee | `<meta name="DC.contributor" content="Raytheon Co" scheme="assignee">`; `<dd itemprop="assigneeOriginal">`; `assigneeCurrent` may be blank |
| Cited patents | `<meta name="DC.relation" content="US:5093563" scheme="references">` (also `US:20030076485:A1`, `WO:2005080928:A1`) |
| Cited non-patent | `<meta name="citation_reference" content="..." scheme="references">` |
| Abstract / claims / description | `<section itemprop="abstract">`, `<section itemprop="claims">` (each claim `class="claim"` with `claim-text` spans; 53 `claim-text` in this patent), `<section itemprop="description">` |
| Backward/forward cites table | `<tr itemprop="backwardReferences">`, `itemprop="forwardReferences"`, `forwardReferencesFamily`, `examinerCited`; `similarDocuments` |
| CPC | `itemprop="classifications"` with `Code`, `Description`, `IsCPC` |
| PDF | `<meta name="citation_pdf_url" content="https://patentimages.storage.googleapis.com/.../US10000000.pdf">` (HTTP 200 confirmed) |

Gotchas: for Google, `DC.date scheme="issue"` exists only for grants; for pubs use `itemprop="publicationDate"`. Meta `DC.title`/`citation_title` were NOT present; use `<title>`. Parse with an HTML parser (BeautifulSoup / lxml), not regex, in the real script. Machine-translated titles for non-English docs (e.g. CN, JP) are Google's; compare fuzzily.

## Unofficial: `xhr/query` (observed, do not ship)
`https://patents.google.com/xhr/query?url=q%3Dtime%2Bof%2Bflight%26num%3D3&exp=` returned HTTP 200 JSON: `results.total_num_results, total_num_pages, cluster[0].result[i].patent{title, snippet, priority_date, filing_date, grant_date, publication_date, inventor, assignee, publication_number, language, thumbnail, pdf, figures, family_metadata}`. Conflicts with robots.txt; may break any time. Documented only so nobody re-tests it.

## BigQuery `patents-public-data` (documented, NOT run)
Google Cloud public dataset `patents-public-data.patents.publications` (plus `google_patents_research`, `uspto_oce_*`). Requires a Google Cloud project and billing/quota (free tier 1 TB queries/month). UNVERIFIED in this session (not run, per instructions). Not keyless; skill should not depend on it.

---

# 2. USPTO Open Data Portal (ODP) - key required

**Covers**: US application/patent bibliographic data, continuity, file wrapper documents (office actions, claims, etc.), assignments, transactions, PTA, foreign priority, attorney, PTAB appeals, petition decisions, bulk datasets. Docs hub: `https://data.uspto.gov/apis/getting-started`, Swagger `https://data.uspto.gov/swagger/index.html`, data dictionary `https://data.uspto.gov/documents/documents/patent-data-schema.json` (all are a JS single-page app; plain curl returns the SPA shell, so I could not read them. Use a browser).
**Base**: `https://api.uspto.gov/api/v1/` (CONFIRMED-LIVE: host answers).
**Access:** use the current [ODP getting-started documentation](https://data.uspto.gov/apis/getting-started) for account/key setup. The helper uses an `X-API-KEY` header supplied through `USPTO_ODP_API_KEY`. Authenticated access was not exercised in this release; verify current requirements before use. Never create an account or expose a key without authorization.
**Rate limits:** consult current service documentation and response headers. Local throttling/backoff does not establish the provider's allowed quota.

## Routes used or recorded by the helpers (authenticated behavior untested)

Unauthenticated 401/403 responses do not establish that a route, parameter set or returned schema is correct. Treat the table as integration notes requiring current documentation and authenticated verification. For examiner research, use the official [Office Action Text Retrieval](https://data.uspto.gov/apis/office-action-retrieval/search) and [Patent File Wrapper](https://data.uspto.gov/apis/patent-file-wrapper/search) pages; see the [Developer Hub to ODP mapping](https://data.uspto.gov/documents/documents/DH-to-ODP-Office-Action-APIs-Mapping.pdf). Legacy Developer Hub routes are retired.

| Purpose | Route |
|---|---|
| Search applications (GET `?q=` or POST JSON) | `GET/POST /patent/applications/search` |
| Search download | `/patent/applications/search/download` |
| Application data (full) | `/patent/applications/{applicationNumber}` |
| Metadata (title, status, dates, assignee) | `/patent/applications/{applicationNumber}/meta-data` |
| Continuity (parents/children) | `/patent/applications/{applicationNumber}/continuity` |
| Documents list (office actions, claims, IDS...) | `/patent/applications/{applicationNumber}/documents` (filters `documentCodes`, `officialDateFrom/To`) |
| Download a document | `/download/applications/{applicationNumber}/{documentId}` (PDF/XML/MS_WORD) |
| Assignments | `/patent/applications/{applicationNumber}/assignment` |
| Transactions / PTA / attorney / foreign priority / associated docs | `/transactions`, `/adjustment`, `/attorney`, `/foreign-priority`, `/associated-documents` |
| Status codes | `/patent/status-codes` |
| PTAB appeals decisions | `/patent/appeals/decisions/search` |
| PTAB trials | `/patent/trials/proceedings/search` unauthenticated response observed; operation/schema unverified |
| Petition decisions | `/petition/decisions/search` |
| Bulk data products | `/datasets/products/search`, `/datasets/products/{productId}`, `/datasets/products/files/{path}` |

Official catalog page (CONFIRMED-DOC, data.gov): Search is "refreshed daily", all patent application bibliographic/front-page fields, 100+ attributes; nine file-wrapper endpoints (Search, Application Data, Continuity, Documents, Transactions, PTA, Address/Attorney, Assignments, Foreign Priority). Public domain license (CC PDM 1.0).

## Query syntax (UNVERIFIED, from patent-client + pyuspto docs)
- `q` = Lucene-like: `inventionTitle:Ball AND filingDate:2024-01-01`; `applicationNumberText:16*`.
- POST body keys: `q`, `filters:[{name,value}]`, `rangeFilters:[{field,valueFrom,valueTo}]`, `sort:[{field,order:"Desc"}]`, `pagination:{offset,limit}`, `fields`, `facets`.
- Default page: offset 0, limit 25.
- Field names seen: `applicationNumberText`, `applicationMetaData` (nested), `applicationTypeLabelName`, `filingDate`. An apis.io sample showed `patentNumber, grantDate, inventionTitle, applicants[].applicantNameText, inventors[].inventorNameText` but its schema (top-level `patents`, `dateRangeData`) looks older; DO NOT hardcode. Script must be written to tolerate nested `applicationMetaData.{inventionTitle,patentNumber,grantDate,filingDate,firstApplicantName...}` and discover keys at runtime.

## Full text
Grant/pub full text is not clearly offered by search; docs endpoint returns file-wrapper docs (incl. patent XML/PDF). Bulk products (`/datasets`) carry full-text grants/pubs (UNVERIFIED). For a single patent's text, Google Patents is easier.

## Verify use
With a key: convert number to application number first (patent number -> search `q=applicationMetaData.patentNumber:...`, UNVERIFIED field path) then `/meta-data`. Compare title, grant date, assignee/applicant. Use `/continuity` for family and `/documents` for claims/office actions.

---

# 3. PatentsView PatentSearch API - DEAD (do not use)

- CONFIRMED-LIVE: `search.patentsview.org` does NOT resolve (`curl: (6) Could not resolve host`). `patentsview.org/apis/purpose` answers 301 (Cloudflare).
- CONFIRMED-DOC (uspto.gov notice 2026-03-18): PatentsView migrated to ODP on March 20, 2026. PatentsView data downloads and data dictionaries are on ODP; "search, APIs, visualizations and support services pause temporarily" with plans to return in updated forms. Transition guide: `data.uspto.gov/support/transition-guidance/patentsview`. Contact `data@uspto.gov`.
- Old API (for history; UNVERIFIED now): `POST/GET https://search.patentsview.org/api/v1/patent/`, header `X-Api-Key`, 45 req/min, fields `patent_id, patent_title, patent_date, cpc_current, ...`. Legacy API ended May 1, 2025. Skill must not call it; if the host ever resolves again, re-verify first. Use ODP bulk data downloads for PatentsView tables.

---

# 4. EPO Open Patent Services (OPS)

**Covers**: bibliographic data, abstracts, claims/description (some jurisdictions), INPADOC family, legal status, number conversion, search (CQL), for 100+ authorities.
**Auth**: free registration at developers.epo.org (cannot reach: Cloudflare challenge "Just a moment..."; I did not register). Flow (CONFIRMED-LIVE as far as unauthenticated probing goes):
- `POST https://ops.epo.org/3.2/auth/accesstoken` with HTTP Basic `consumerKey:consumerSecret` and body `grant_type=client_credentials`. With bad creds -> `401 <error><code>401</code><message>ClientId is Invalid</message>` (so endpoint and Basic-auth flow are real). GET -> 404.
- Then `Authorization: Bearer <token>` on `https://ops.epo.org/3.2/rest-services/...`. Bad token -> `400 invalid_access_token` (CONFIRMED-LIVE). No token -> `403 ... violation of Fair Use policy` (CONFIRMED-LIVE, misleading message).
- Token lifetime (about 20 minutes) and success-response fields (`access_token`, `expires_in`) UNVERIFIED by me; read `expires_in` at runtime.
**Quota** (CONFIRMED-DOC, EPO fair-use + OPS pages): non-paying users up to 4 GB/week (calendar week Mon 00:00 to Sun 24:00 GMT); paid subscription EUR 2,800/yr above. Family actions: threshold one request/second. Dynamic fair-use throttling. Terms: `epo.org/en/service-support/ordering/ops-terms-and-conditions`.
**Endpoints** (UNVERIFIED by live call, I had no credentials; from my knowledge of OPS 3.2, confirm against the OPS 3.2 Reference Guide before coding):
- Biblio: `GET /3.2/rest-services/published-data/publication/{epodoc|docdb|original}/{number}/biblio`
- Family: `GET /3.2/rest-services/family/publication/epodoc/{number}`
- Legal: `GET /3.2/rest-services/legal/publication/epodoc/{number}`
- Number conversion: `POST /3.2/rest-services/number-service/...`
- Responses are XML by default; send `Accept: application/json` for JSON.
**Terms note**: free for use; do not bulk-harvest. **Verify use**: biblio gives title (`invention-title`), `publication-reference` date, `applicant-name` (assignee). Needs user-provided key/secret in env vars.

---

# 5. Lens.org API

**Covers**: patents + scholarly works, citation links, families. Docs `https://docs.api.lens.org/` (v2.19.3, updated 2026-04-17 per search snippet).
**Auth**: bearer token required. CONFIRMED-LIVE: `POST https://api.lens.org/patent/search` and `/scholarly/search` return `401 {"message":"Missing/Incorrect Authorization Header"}`. Access is requested from a Lens user profile; plans/prices not confirmed (UNVERIFIED). Cambia reportedly sold Lens to a non-profit in 2026 (single source, UNVERIFIED).
**Use**: optional cross-check only, with `LENS_TOKEN`. Do not request an account for the user.

# 6. WIPO PATENTSCOPE

- No open public JSON API found. WIPO describes a SOAP-based Java API for PATENTSCOPE publication documents under subscription (CONFIRMED-DOC via search snippet; details/fees UNVERIFIED). PCT-data subscriber terms restrict to 10 retrieval actions/min per IP (snippet; UNVERIFIED applicability).
- `https://patentscope.wipo.int/search/en/search.jsf` HTML loads (CONFIRMED-LIVE) but is JSF/session-based; scraping it is not advised and terms say WIPO may block abusive use; credit "WIPO PATENTSCOPE Database".
- For WO numbers use Google Patents `/patent/WO2020123456A1/en` (200 confirmed) or EPO OPS.

# 7. USPTO Patent Public Search (ppubs.uspto.gov)

- Web app loads (`/pubwebapp/` and `/pubwebapp/external.html` return 200, CONFIRMED-LIVE). `robots.txt` returns 404 (no rules published).
- No documented public JSON API. An internal JSON backend exists for the web app, but it is undocumented, and USPTO has historically prohibited automated scraping of PPUBS; I could not read the terms page in this session (UNVERIFIED). Policy for the skill: do not scrape or call the internal PPUBS endpoints. Send the user a manual link only. Use ODP for sanctioned programmatic access.

---

# 8. Scholarly + web-dating sources (keyless, all CONFIRMED-LIVE 2026-11-18)

| Source | Request | Result |
|---|---|---|
| OpenAlex | `GET https://api.openalex.org/works?search=time+of+flight+camera&per-page=1&select=id,doi,title,publication_date,type` | 200. Keyless shares a tiny free daily budget ($0.10) per IP; free key available by the user's request (do not create). Look up by DOI: `/works/doi:10.xxx`. Fields: `id, doi, title, publication_date, type, authorships`. |
| Crossref | `GET https://api.crossref.org/works?query=...&rows=1` or `/works/{DOI}` | 200. Fields `DOI, title[], issued.date-parts, container-title`. Add `mailto=` param only if the user supplies an email (do not invent). Note: `select=` gave a sparse item; fetch without select. |
| Semantic Scholar | `GET https://api.semanticscholar.org/graph/v1/paper/search?query=...&limit=1&fields=title,year,externalIds,publicationDate` | 429 Too Many Requests on first keyless call (shared pool). Treat as optional, retry later; key optional for higher limits. |
| arXiv | `GET https://export.arxiv.org/api/query?search_query=all:holography&max_results=1` | 200 Atom XML. `entry/id, title, published, updated, author`. Lookup by id: `id_list=2509.20517`. Keep to 1 req / 3 s. |
| Wayback CDX | `GET https://web.archive.org/cdx/search/cdx?url=example.com&limit=2&output=json&from=2015` | 200 JSON array; header row `urlkey,timestamp,original,mimetype,statuscode,digest,length`. First timestamp = earliest capture (e.g. `20150101000457`). Use `&sort=...` default ascending; `&filter=statuscode:200` for real pages. |
| Wayback availability | `GET https://archive.org/wayback/available?url=example.com&timestamp=20150101` | 200 `archived_snapshots.closest{status,available,url,timestamp}`. |

Prior-art dating rule for scripts: a web page's date = earliest Wayback capture with status 200 unless the page itself carries an earlier verifiable date; a Wayback capture proves the content existed no later than that timestamp.

---

# 9. Number formats (for normalize_number.py)

Canonical output: `{country, number, kind, type}` and a Google-style key `US10000000B2`.

**US granted patents**: 7 digits for utility (`US10000000`, since 2018: 8 digits; seen as `US 11,234,567 B2`). Kind: `B1` (no prior pub), `B2` (prior pub), `A` (pre-2001 grants, no kind), `E`/`E1` (reissue, old), `RE` prefix: `RE47,123` or `USRE47123E`/`USRE47123E1` (6 digits after RE); `S` design `USD912345S` (D + 6-7 digits; kind `S1`); `P`/`P2`/`P3` plant (`USPP12345P2`); `H` SIR (`USH1234H`); `X` early. Strip commas/spaces.
**US pre-grant publications**: 11 digits `YYYYNNNNNNN` since 2001: `US 2023/0123456 A1` -> `US20230123456A1`. Kinds `A1` (pub with search report), `A2` (without), `A9` (corrected), `P1` plant pub. Older form in Google: `US20030076485A1`. Pad the serial to 7 digits when given `2023/123456`.
**US application numbers**: `16/123,456` (series code 2 digits + 6 digits; series 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19; 29/ for design; 60-63/ provisional `63/123,456`; 35 PCT US designs `PCT/US2019/012345` -> `PCTUS1912345` in ODP-style `PCTUS19012345`). ODP uses digits only: `16123456`; example verified in Google: `US:14/643,719` -> `14643719`. 61/60 etc. provisionals have no publication.
**EP**: `EP1000000A1` / `EP1000000B1` (7 digits; app `EP19123456.7`, 8 digits + check digit; `EP 3 456 789 B1`). Kinds A1 (with search report), A2, A3 (search report only), A4, B1 (granted), B2 (amended), B3 (limitation). Spaces/dots stripped.
**WO/PCT**: publication `WO2020123456A1` (since 2002: `WOYYYYNNNNNN`, 4-digit year + 6 digits; pre-2002 `WO 99/12345` -> `WO1999012345`); kinds A1, A2, A3. Application `PCT/US2019/012345` (country, 4-digit year, 5-6 digits; older `PCT/US99/12345`).
**CN**: pub `CN101234567A` (9 digits; kinds A applicat., B granted invention (pre-2007 `C`), U utility model, S design, `Y` older UM); app `CN201910123456.7` (12 digits + dot + check digit).
**JP**: `JP2020123456A` (year + 6 digits; era years for older `JPH0123456A`, `JPS6012345A`; Heisei `H`, Showa `S`); granted `JP6789012B2`; app `JP2019-123456` -> `JP2019123456`.
**KR**: `KR1020200012345A` (10 + 4-digit year + 7 digits for pubs; `KR102123456B1` granted, 9 digits); app `KR10-2019-0012345`.
**Kind-code semantics differ by office** (A = pub, B = grant in most; US kind meanings changed in 2001). Never infer grant vs pub without the kind + digit count. 11 digits starting 20xx => US pub; 7-8 digits => US grant.
**Normalization steps**: uppercase; strip spaces, commas, hyphens, slashes except for app numbers; detect `RE`, `D`, `PP`, `H`, `X`; detect `PCT/`; return both `google_id` (country+number+kind) and `odp_application_digits` where applicable. When kind is missing, try `B2` then `B1` then `A1`; on Google, bare `US10000000` also resolves (200), so check kind from `<title>`.

---

# 10. Test log (2026-11-18)

| Test | Result |
|---|---|
| Google Patents US10000000B2 HTML | 200, meta tags parsed (see above) |
| Google robots.txt | `/patent/` allowed, `/*` disallowed |
| ODP no key | 401 `Unauthorized` / 403 `Forbidden` (documents) / 403 `Missing Authentication Token` for bogus path |
| ODP dev host `api-dev.uspto.gov` | does not resolve |
| PatentsView search host | does not resolve |
| EPO token with bad creds | 401 `ClientId is Invalid` |
| EPO biblio no/invalid token | 403 fair-use msg / 400 `invalid_access_token` |
| Lens search no token | 401 |
| OpenAlex, Crossref, arXiv, Wayback CDX + availability | 200 |
| Semantic Scholar | 429 |
| developers.epo.org, data.uspto.gov docs | Cloudflare/SPA, not readable by curl |
