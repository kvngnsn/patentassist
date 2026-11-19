---
title: Field guide - software, AI, and networked systems
last_verified: 2026-11-18
sources:
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2106.html
    supports: MPEP 2106 eligibility framework; 2106.03 transitory signals not statutory (In re Nuijten; Mentor Graphics v. EVE-USA).
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2181.html
    supports: MPEP 2181 generic placeholders ("module for", "unit for", etc.) may invoke 112(f); computer-implemented 112(f) needs a disclosed algorithm.
  - url: https://www.uspto.gov/web/offices/pac/mpep/s2164.html
    supports: MPEP 2164.06(c) enablement issues in computer programming cases.
  - url: https://www.ecfr.gov/current/title-37/section-1.96
    supports: 37 CFR 1.96 program listings; over 300 lines must go in a Computer Program Listing Appendix (ASCII text).
  - url: references/eligibility-101.md
    supports: Current USPTO 101 guidance, memos, Desjardins, and 2025-2026 Federal Circuit cases (not repeated here).
---

# Field guide: software, AI, networked systems

Load at Phase 3, Round 4 (claim categories) and again at Step 3 (spec). Rules in `claim-drafting.md` and `specification-drafting.md` apply; this file adds what is specific to software.

## Default claim categories

| Claim | Default | Notes |
|---|---|---|
| Method (one actor) | yes | server-side or device-side, never both in one claim |
| System (processor + memory with instructions) | yes | parallel to the method |
| Non-transitory computer-readable medium | yes | must say "non-transitory" |
| Second-actor method | when the other side is a product too | e.g., client app method plus server method |
| Data structure or message format | rarely | only as part of a method or system claim |

Budget: 3 independents (method, system, CRM) inside 20 claims, unless the user pays for more.

## What examiners in this field focus on

- **101 eligibility.** The main risk. The examiner asks whether the claim recites an abstract idea (math, mental process, organizing human activity) and, if so, whether it integrates it into a practical application. Current guidance and cases: `eligibility-101.md`.
- **103 combinations.** Software claims are often rejected as a combination of two or three references with a "known technique" rationale.
- **112(f) and 112(b).** "Module," "engine," "unit," "component," or "logic" plus a function, with no structure, can trigger 112(f). Without an algorithm in the spec, the claim is indefinite (MPEP 2181).
- **112(a) for result-style claims.** Claims that recite a result ("determine the optimal route") without how. Written description and enablement attacks follow.

## Typical 101 and 112 risks and fixes

| Risk | Looks like | Fix |
|---|---|---|
| Abstract idea on a computer | "receiving data, analyzing it, displaying a result" | Claim the specific technical mechanism: data structures, ordering, resource handling, a specific model input/output pipeline that changes how the computer or network operates |
| Result without means | "using machine learning to predict X" | Recite the model inputs, how they are built, the training or inference steps that matter, and what the output controls |
| Business method framing | "a method of managing payments" | Recast around the technical problem (latency, bandwidth, security, memory) and the technical solution, if the invention really has one. If it does not, say so honestly (Phase 1 Check B). |
| Nonce words | "a scheduling module configured to …" | "a processor configured to execute instructions that cause the processor to …", plus an algorithm in the spec |
| Signals | "a computer-readable medium storing …" | "a non-transitory computer-readable medium …"; define it in the spec to exclude transitory signals |
| Divided steps | user does step 1, server does step 2 | one actor per claim (`claim-drafting.md` Section 7) |
| Undetectable claims | internal server logic only | add a claim to the detectable output or device behavior, or weigh trade secret |

## AI and machine learning specifics

- Decide which part is new: the model architecture, the training data or labeling method, the training procedure, the inference deployment, or the use of the output to control something. Claim that part directly.
- Describe in the spec: inputs and how they are preprocessed, model type and key structure, loss or training objective, training data characteristics (without trade secrets the user wants to keep), inference flow, how outputs are thresholded or used, and alternatives for each.
- Give at least one concrete technical effect with numbers if the inventor has them (latency, memory, accuracy, energy). State working results in past tense only if they were actually measured.
- Inventorship: ask how AI tools were used in conception (`ai-and-inventorship.md`).

## Figures to include

| Figure | Shows | Supports |
|---|---|---|
| System block diagram | devices, servers, networks, data stores, and connections | system claims |
| Flowchart per method | each step with a numeral, decision branches | method and CRM claims, algorithm disclosure |
| Sequence diagram | messages between actors over time | single-actor drafting, protocol claims |
| Data structure diagram | records, fields, keys, message formats | specific technical mechanism (101) |
| Model or pipeline diagram | data flow through preprocessing, model, postprocessing | AI claims |
| UI wireframe | user-facing features as line art | UI claims |
| Hardware diagram | processor, memory, storage, network interface, sensors | hardware context, structure for 112(f) |

`drawings.py` generates flowchart, block, sequence, wireframe, and graph types (`state-files.md` figure plan).

## Specification must-haves

- [ ] An algorithm for every claimed function: steps, conditions, data, and order (flowchart + prose; pseudocode helps).
- [ ] Data structures and formats that make the improvement work.
- [ ] Hardware context: where each step runs (device, edge, server), processor and memory, network.
- [ ] The technical problem and the technical improvement, stated plainly, with measurable effects where available.
- [ ] Alternatives: other algorithms, models, thresholds, orderings, deployment locations.
- [ ] Definitions for construction-dependent terms (module, engine, service, agent, model, pipeline).
- [ ] The computing boilerplate (software, hardware, or both; non-transitory media) from `specification-drafting.md` Section 7.
- [ ] No full source code in the spec. Short pseudocode is fine. A real program listing over 300 lines must go in a Computer Program Listing Appendix as an ASCII text file (37 CFR 1.96).

## Disclosure traps in software

- Public repos, package releases, app store or beta releases, demos, blog posts, and conference talks all start the clock (`bars-and-eligibility.md`).
- Open-sourcing the code publishes the method. Decide on patent versus trade secret before release.
- Investor decks shown without an NDA can count as disclosures.
