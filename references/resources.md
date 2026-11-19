---
title: Other AI tools and free patent research resources
last_verified: 2026-11-19
sources:
  - https://github.com/anthropics/claude-for-legal
  - https://github.com/RobThePCGuy/Claude-Patent-Creator
  - https://github.com/LeonardHope/Claude-Skill-for-Patent-Examiner-Intelligence
  - https://github.com/alirezarezvani/claude-skills
  - https://www.uspto.gov/patents/search/patent-public-search
  - https://www.epo.org/en/searching-for-patents/technical/espacenet
  - https://www.wipo.int/en/web/patentscope
---

# Other tools and research resources

These are optional alternatives and complements. PatentAssist does not require them or bundle their code. Descriptions reflect public documentation reviewed on the date above; external projects were inspected, not installed or benchmarked. A free/open-source skill is not necessarily a free hosted service. Check current licensing, access, model costs and how a service handles confidential inventions before using it.

## AI skills and open-source projects

| Resource | What it does | Access and practical limits |
|---|---|---|
| [Anthropic invention-intake](https://github.com/anthropics/claude-for-legal/blob/main/ip-legal/skills/invention-intake/SKILL.md) | Structured inventor interview covering mechanisms, development, contributors and disclosures. Useful before searching or drafting. | [Apache-2.0 project](https://github.com/anthropics/claude-for-legal/blob/main/LICENSE). Designed for Claude's legal workflow; its intake instructions can inform other agents, but host-specific integrations need adaptation. It expressly excludes patent-claim drafting. Model/host access is separate. |
| [Claude Patent Creator](https://github.com/RobThePCGuy/Claude-Patent-Creator) | Patent research/drafting workflow with MCP tools, legal-material retrieval, prior-art search, document/diagram generation and automated checks. | [MIT](https://github.com/RobThePCGuy/Claude-Patent-Creator/blob/main/LICENSE). A more involved Claude-oriented setup; documented features use model, database and optional compute services. Free source code does not make those services free or prove legal accuracy. |
| [Patent Examiner Intelligence](https://github.com/LeonardHope/Claude-Skill-for-Patent-Examiner-Intelligence) | Examiner profiles and dashboards assembled from patent/prosecution data, with source/provenance reporting. Useful for examining public prosecution patterns. | [MIT](https://github.com/LeonardHope/Claude-Skill-for-Patent-Examiner-Intelligence/blob/main/LICENSE). Designed as a Claude skill; source access/credentials and adaptation may be needed elsewhere. Historical allowance/interview patterns do not prove a strategy caused an allowance or predict your claim's outcome. |
| [Open-source patent research skill](https://github.com/alirezarezvani/claude-skills/blob/main/research/patent/skills/patent/SKILL.md) | A research workflow using technical vocabulary, classifications, citations and patent families; useful as another search-plan reference. | [MIT collection](https://github.com/alirezarezvani/claude-skills/blob/main/LICENSE). Check the current skill's host/tool requirements. Assess whole claim combinations rather than treating keyword overlap or separately known components as a legal conclusion. |

These tools can help generate research notes or application drafts; none can promise a grant. PatentAssist's workflow stays model-agnostic even where an optional linked project targets a named model or host. A capable local-model agent can load this repository's Markdown and Python helpers; live research still requires permitted source access, and document-only/offline work must disclose its coverage limits.

## Free public patent research

| Resource | Useful for | Limits |
|---|---|---|
| [Google Patents](https://patents.google.com/) | Broad patent full-text discovery, classifications, related documents, citations and families. | Free web interface; retrieval limits apply. Verify critical dates, translations, legal status and passages against authoritative records. |
| [EPO Espacenet](https://www.epo.org/en/searching-for-patents/technical/espacenet) | Worldwide patent searching, CPC exploration, families and citation trails. | Free web search. Separate EPO APIs have their own registration, terms and quotas. |
| [WIPO PATENTSCOPE](https://www.wipo.int/en/web/patentscope) | PCT applications and participating national/regional collections, including multilingual searching. | Free research interface; some features/access conditions vary. It is not an exhaustive legal-status or freedom-to-operate opinion. |
| [USPTO Patent Public Search](https://www.uspto.gov/patents/search/patent-public-search) | Official US patent/application searching with basic and advanced interfaces and training materials. | Free web tool; US coverage does not replace foreign and nonpatent research. |
| [USPTO Open Data Portal](https://data.uspto.gov/apis/getting-started) | Public prosecution/file-wrapper data and office-action retrieval for source-backed research and evaluation. | API access requires the applicable account/key setup. Use current ODP routes; legacy Developer Hub routes are retired. Public metadata is not a complete argument corpus. |

## Learn the examiner's reasoning

- [USPTO MPEP](https://www.uspto.gov/web/offices/pac/mpep/index.html): the Office's examination manual. Useful starting sections include [claim interpretation](https://www.uspto.gov/web/offices/pac/mpep/s2111.html), [anticipation](https://www.uspto.gov/web/offices/pac/mpep/s2131.html), [obviousness](https://www.uspto.gov/web/offices/pac/mpep/s2143.html), [applicant rebuttals](https://www.uspto.gov/web/offices/pac/mpep/s2145.html), and [enablement](https://www.uspto.gov/web/offices/pac/mpep/s2164.html). Agency practice is not a substitute for controlling statutes and cases.
- [Examiner training](https://www.uspto.gov/learning-and-resources/examiner-training-materials) and [STEPP](https://www.uspto.gov/patents/training/stepp): public training materials and programs explaining examination methods. Check program eligibility/availability separately.
- [Office Action Research Dataset](https://www.uspto.gov/ip-policy/economic-research/research-datasets/office-action-research-dataset-patents): historical research data, discontinued and covering 2008–mid-2017. Useful for historical analysis, not current individual-examiner predictions.

See [examiner-review.md](examiner-review.md) for the reasoning procedure and proposed public-data evaluation design. No claimed real-world accuracy score is derived from these links.
