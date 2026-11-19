---
title: Case law index: how to think like a patent lawyer
last_verified: 2026-11-18
sources:
  - Case selection follows a standard US patent-law casebook (17 chapters, about 110 principal cases plus note cases). Every digest is original writing; holdings were checked against the opinions and their current status as of the date above.
---

# Case law index

These files exist so the skill reasons like an experienced patent lawyer: it knows the leading cases, where each rule stops, which fact flips the outcome, and what a naive analysis gets wrong. Each file has per-case entries (facts, rule, nuance, status, **skill rule**), then an **edge-case playbook**, post-casebook developments, and a checklist.

**How to use them.** Load a file at the step that needs it (table below). Before a verdict, chart, claim set, or reply goes out, run that file's edge-case playbook against the facts: "Does any trap here apply?" Cite cases only as these files state them. Any case not in these files goes through the normal verification rule (SKILL.md source-verification requirements: fetch or verify it, or tag it `[memory – verify]`).

| File | Doctrine | Load at |
|---|---|---|
| `eligibility-and-utility.md` | §101 (Chakrabarty, Benson, Mayo, Myriad, Alice and progeny), utility (Brenner, Fisher, Juicy Whip), patent vs trade secret, preemption | Phase 1 Check B · Phase 3 claims (software, AI, diagnostics) · office actions with 101 rejections |
| `anticipation.md` | one-reference rule, inherency, genus/species, enabling prior art, arrangement as claimed | Phase 1 Check C verdict · Phase 2 analysis · invalidity charts |
| `novelty-and-bars.md` | AIA 102(a)/(b), public use, on-sale (incl. secret sales), printed publication, experimental use, 102(a)(2), pre-AIA 102/priority contests, date mechanics | Phase 1 Check A · Phase 2 cutoff and prior-art basis · invalidity mode |
| `obviousness.md` | Graham, KSR, analogous art, motivation, obvious-to-try, secondary considerations and nexus, chemical obviousness | Phase 2 103 analysis · Phase 3 self-attack · office actions with 103 rejections |
| `specification-112.md` | enablement (Wands, Amgen), written description (Vas-Cath, Ariad), best mode, provisional support | Phase 3 spec · provisional decisions · office actions with 112(a) rejections |
| `claims-and-construction.md` | claim formats, preambles, means-plus-function (Aristocrat, Williamson), definiteness (Nautilus), construction (Markman, Phillips, Teva), disavowal and lexicography | Phase 3 claims · all claim charts · FTO · office actions with 112(b) or 112(f) |
| `prosecution.md` | continuations and new matter, inventorship, inequitable conduct (Therasense), double patenting, priority, reissue | Phase 3 filing decisions · office-action tool · IDS duty |
| `ptab.md` | IPR/PGR (Oil States, Cuozzo, SAS, Arthrex), amendment practice, estoppel, discretionary denial | invalidity mode · FTO next steps · portfolio risk |
| `infringement.md` | all-elements rule, DOE, Festo estoppel, dedication-disclosure, ensnarement, inducement and contributory infringement, divided infringement, 271(f), venue | FTO screen · infringement charts · drafting (single-actor claims, claim the detectable side) |
| `defenses.md` | experimental use, safe harbor, misuse, laches, exhaustion, repair vs reconstruction, prior user §273, assignor estoppel | FTO screen · analysis · licensing questions |
| `remedies.md` | injunctions, lost profits, reasonable royalty, apportionment, willfulness (Halo), fees (Octane), marking (Amsted) | FTO willfulness warnings · portfolio (marking) · risk framing |
| `design-patents.md` | ordinary observer, functionality, obviousness after LKQ, article of manufacture | routing design questions (US utility is the scope; give facts and refer) |
| `pharma-and-sep.md` | Hatch-Waxman, BPCIA, skinny labels, SEP/FRAND | FTO in pharma, biotech, telecom · drafting around standards |
| `edge-case-drills.md` | recurring exam-style traps, date-mechanics drills, issue-spotting drills | before any verdict involving dates · self-review in every phase |

## Ten habits these cases teach

1. **Read the claim, not the invention.** Every validity and infringement question is asked claim by claim, element by element.
2. **Dates decide more cases than technology does.** Compute effective filing dates, grace periods, and priority claim by claim before judging novelty.
3. **One reference, every element, as arranged.** Anything less is a 103 question, not a 102 one.
4. **Inherency needs necessity, not probability.**
5. **For 103, ask "why would someone combine these?"** The answer must come from the record, not from the invention's own teaching (hindsight).
6. **Words get litigated.** Each claim term will be read in light of the spec and the prosecution history. Define the terms you need, and never disparage an embodiment you want to keep.
7. **Functional language without structure is a trap** (112(f), Williamson). For software, that means disclosing the algorithm.
8. **Every argument and amendment in prosecution can narrow the patent later** (Festo, disclaimer). Say less, and say it precisely.
9. **Infringement needs one actor, or direction or control** (Akamai). Draft claims so a single competitor practices every step.
10. **Status beats memory.** Check whether a case was later limited or overruled before relying on it. Each entry here records that status.
