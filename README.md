# PatentAssist — AI patent research, prior-art search and drafting

A model-agnostic agent skill for US utility-patent research and drafting. It clarifies the inventor's actual idea, searches prior art, gives candid evidence-backed assessments, and prepares supported application drafts.

[![Download](https://img.shields.io/github/v/release/kvngnsn/patentassist?label=download)](https://github.com/kvngnsn/patentassist/releases/latest) [![License](https://img.shields.io/badge/license-MIT%20%2B%20CC0-blue)](LICENSE) [![Agent Skills](https://img.shields.io/badge/Agent%20Skills-portable-2d6a4f)](https://agentskills.io/specification)
[![Checks](https://github.com/kvngnsn/patentassist/actions/workflows/check.yml/badge.svg)](https://github.com/kvngnsn/patentassist/actions/workflows/check.yml)

**Start here:** [install](#install) · [workflow](SKILL.md) · [other AI tools and free research](references/resources.md) · [download](https://github.com/kvngnsn/patentassist/releases/latest)

For inventors, patent lawyers and researchers who need a clear patentability assessment, claim-scope analysis or supported patent application draft. Covers invention intake, prior art, examiner objections, applicant responses and drafting; keeps real matter files outside the repository.

| Phase | What it does |
|---|---|
| **0 · Clarify** | Ask focused questions; separate known facts, suggestions and unknowns; screen eligibility, disclosure readiness and possible deadlines without prior-art searching. |
| **1 · Quick search** | Find decisive references and explain what they mean for the current formulation. |
| **2 · Deep analysis** | Assess the claimed combination, test novelty/obviousness arguments, and agree useful scope. |
| **3 · Draft** | Develop claims, specification and figures together, with support and consistency checks. |

**Every phase includes:** bottom line → strongest examiner objection → strongest supported applicant response → resolution → next action. No separate final-review phase. “Likely unpatentable as currently formulated” is a legitimate result; a favorable scoped assessment is permitted when the reviewed evidence supports it. A limited search finding nothing is not proof of patentability.

The skill asks for missing mechanisms instead of silently inventing a different invention. Material changes reopen the affected analysis. It also provides optional FTO/invalidity, office-action, patent-summary and docketing workflows.

## Install

**Claude Code**

```sh
git clone https://github.com/kvngnsn/patentassist.git ~/.claude/skills/patentassist
```

**Codex**

```sh
git clone https://github.com/kvngnsn/patentassist.git ~/.agents/skills/patentassist
```

Open a new session and invoke `/patentassist` or `$patentassist` respectively. For another host, use the [release ZIP](https://github.com/kvngnsn/patentassist/releases/latest) or point a capable agent directly to [SKILL.md](SKILL.md). Existing installations should be updated in place rather than duplicated.

## Use with your model

The workflow uses portable Markdown and Python, with no required AI provider, model or agent CLI. A suitably capable local-model agent can use the same files. Full operation needs file access, Python execution and source retrieval; a text-only host can discuss supplied documents but cannot complete the automated checks or live search. Quality depends on the model, evidence and review.

Example prompts:

> Use PatentAssist. Help me clarify this invention before searching. Ask about missing mechanisms; do not add features I have not described.

> Use PatentAssist. Search this confirmed invention. Tell me plainly whether the current scope looks likely patentable or unpatentable, show the strongest objection and response, and resolve the conflict.

> Use PatentAssist. Draft from this disclosure and search record, preserving my invention. Explain every material narrowing and reassess the claims as they change.

Create matter files **outside this repository**. Default: `~/Desktop/PatentAssist/<matter>/`; any chosen private directory works. Scripts accept `--dir`. Existing state/decisions can be resumed across sessions and models.

```sh
# Optional document/PDF tools; put the environment outside the repository.
python3 -m pip install -r requirements.txt
python3 scripts/state.py init --title "My invention" --dir /chosen/private/matter
```

Python 3.9+; most search/state helpers use the standard library. Optional source credentials: `USPTO_ODP_API_KEY`, `EPO_OPS_KEY`/`EPO_OPS_SECRET`, `LENS_TOKEN`. Set them in your environment; never add actual keys to source. Missing services are reported as coverage gaps. No API key is needed for the basic public-web search workflow when the host provides web search.

## Other AI tools and free research resources

See [the resources guide](references/resources.md) for short descriptions, source/license links, access requirements and limitations. It includes Anthropic's invention-intake skill, open-source patent drafting/research projects, examiner-data tools, Google Patents, Espacenet, WIPO PATENTSCOPE and USPTO resources. These are optional alternatives, not dependencies or endorsements. Free/open-source code may still require paid model or data services.

## Repository map

- [SKILL.md](SKILL.md): portable entry point and routing.
- `phases/`: clarification, quick search, deep analysis and drafting.
- [Examiner review](references/examiner-review.md): evidence standards, counterarguments and assessment rules.
- `modules/`, `references/`, `templates/`: supporting workflows and maintained research aids.
- [scripts/README.md](scripts/README.md): deterministic search, document and verification helpers.
- `tests/`, `evals/`: offline regression tests and behavioral scenarios.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_release.py
```

Tests check mechanics, source accounting, review freshness and representative synthetic scenarios. They do not establish real-world legal accuracy, complete search coverage or a calibrated grant probability. The proposed public-prosecution-family evaluation has not been run. Versioned reviews validate fields/source flags/hashes, not the truth of legal reasoning. A passing format checker does not mean a patent will issue.

## Boundaries and license

Outputs are research aids and drafts, not a guarantee or a registered practitioner's opinion. The human decides, signs, files and pays. The workflow never automatically publishes an invention. Source queries follow the user's confidentiality authorization; full disclosures/files are not uploaded without authorization. Source access and current legal rules must be checked for the actual matter.

Scripts/tests: MIT. Original instructions/templates/references: CC0 1.0. Third-party patent documents and cited materials retain their own rights; external linked projects have their own licenses. See [LICENSE](LICENSE) and [fixture provenance](tests/fixtures/README.md).

## Related open-source skills

| Project | Use it for |
|---|---|
| [no-slop](https://github.com/kvngnsn/no-slop) | Clear AI writing and editing, with facts and meaning preserved. |
| [click-everything](https://github.com/kvngnsn/click-everything) | Exploratory UI testing, reproducible bugs and regression tests. |
| [startupassist](https://github.com/kvngnsn/startupassist) | Startup legal documents, founder equity and financing templates. |

## Atlas workflow catalog

The optional [Atlas adapter](atlas/README.md) catalogs individual outputs and future shells. It preserves this standalone skill; adapter readiness is tracked separately.
