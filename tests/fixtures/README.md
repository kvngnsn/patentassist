# Test fixture provenance

`build/`, `draft/` and `prosecution/` contain synthetic examples for parser, formatting and consistency tests. Names, example.com email addresses and street addresses there are fictional test data, not client matters. Their legal outcomes are not real-world findings.

Public document fixtures (retained for reproducible parser/column-line tests):

| File | Public source | Purpose |
|---|---|---|
| `search/US9457709B2.html` | [Google Patents](https://patents.google.com/patent/US9457709B2/en) | Metadata, citations, claim/description parsing |
| `search/US20160144773A1.html` | [Google Patents](https://patents.google.com/patent/US20160144773A1/en) | Published application parsing |
| `search/EP1000000B1.html` | [Google Patents](https://patents.google.com/patent/EP1000000B1/en) | Foreign patent/family parsing |
| `colline/US9457709B2.pdf` | [Patent record and linked PDF](https://patents.google.com/patent/US9457709B2/en) | PDF columns/line-pinpoint extraction |
| `colline/US5560126A.pdf` | [Patent record and linked PDF](https://patents.google.com/patent/US5560126A/en) | Older PDF extraction |

HTML fixtures have scripts/styles removed. Patent identifiers, public bibliographic names, text and source links are intentional source data. These files are third-party/source material, excluded from this repository's MIT/CC0 grants. No assertion is made that every patent document or web presentation is public domain; original notices and rights remain applicable. The repository's fixtures are not a patent database or legal-status service.
