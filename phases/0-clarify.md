# Phase 0: clarify the invention and assess readiness

Read the shared [examiner review](../references/examiner-review.md). This phase uses the user's information and current legal materials; it does not perform prior-art searches or decide novelty/obviousness. If the user supplies art, preserve it for Phase 1 without silently converting the intake into a search.

## Capture the actual invention

Create/read the private matter with `state.py init --title "..." --dir /private/matter`. Set `phase clarify`. Record mode (inventor/practitioner), confidentiality and relevant disclosure/sale/public-use/filing facts. The short date screen is provisional until qualifying events and exceptions are examined.

Ask two to four consequential questions per round; skip established facts. Begin with the user's own explanation. Adapt the sequence:

- What problem is solved, and for whom? What happens from input/start to output/result?
- What parts, steps, relationships or mechanism make that happen? Which details are still unknown?
- Which features define the idea, which are optional, and which alternatives did the user actually contemplate?
- What is different from approaches the user already knows? This is their hypothesis, not a novelty finding.
- What has been built, tested, sketched or merely proposed? A prototype is not an automatic prerequisite; don't invent tests or demand unnecessary implementation detail.
- What would make our description a different invention from the one intended? Who contributed each feature or concept?

Use [invention-disclosure.md](../templates/invention-disclosure.md). For each material feature record its origin, the exact user/source location, whether the user confirmed it, what is unknown, and whether it is essential or optional. Preserve the original explanation alongside the refined one. Suggested ideas stay in a separate proposal section. Never cure an eligibility/support problem by silently inserting a sensor, algorithm, architecture or other invented mechanism.

## Preliminary screen and response

Lead with the specific preliminary result: needs clarification, eligibility concern, disclosure concern, bar concern, or ready to search. Do not lead Phase 0 with an overall “likely patentable” or “likely unpatentable” verdict: no prior-art review has occurred and claim scope may still be undefined. You can state plainly that the current description does not support the requested breadth under §112, or that an identified §101 obstacle is serious. Separate that ground-specific concern from any novelty/obviousness assessment.

Assess current scope for statutory-category/eligibility risk, specific credible utility, and disclosure readiness: can the described mechanism plausibly be explained sufficiently for the intended breadth? Written description and enablement are separate questions; neither is established by a fluent summary. Check inventor/contributor uncertainties and possible deadlines. Read the applicable current primary sources before a legal conclusion.

For each serious issue give the examiner-style objection, the best response supported by current facts, and a resolution. Ask the next question that could change that resolution. No forced rebuttal if the necessary mechanism is unknown. Do not infer novelty/obviousness from enthusiasm, complexity, apparent usefulness or an absence of supplied art.

Outputs: `ready_to_search`, `needs_clarification`, `eligibility_concern`, `disclosure_concern`, or `bar_concern`. These may be explained together in prose; the recorded outcome identifies the next controlling issue. Always state “Novelty and nonobviousness have not been assessed.”

## Confirm scope and preserve the review

Show a concise restatement with core features, optional variants, unresolved facts, and changes from the user's original words. Ask for correction/confirmation unless their prior instruction and supplied disclosure already settle those points. Confirmation establishes what the user intends, not patentability or inventorship by itself.

Write a review JSON following [assessment.json](../templates/assessment.json), then:

```
python3 /path/to/skill/scripts/review.py record --phase clarify --input /private/matter/assessment-input.json --dir /private/matter
python3 /path/to/skill/scripts/state.py set phases.clarify.status done --dir /private/matter
python3 /path/to/skill/scripts/state.py decide --gate clarify --choice "Confirmed brief; quick search authorized" --dir /private/matter
```

Record only the user's actual choice. Proceed if searching is already authorized and the brief is sufficiently defined. Otherwise offer the consequential options. Reopen this phase whenever a substantive missing fact or proposed change affects the invention.
