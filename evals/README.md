# Evaluation

`scenarios.json` contains synthetic behavioral scenarios and observable acceptance criteria. Give a fresh model only the scenario's `input` plus SKILL.md and supplied raw artifacts; keep the rubric separate. Store runs outside this repository. No scenario is a real patent or a calibrated grant prediction.

Check: a direct scoped assessment, strongest supported objection and response, resolution, inventor fidelity, honest search limits and current review versions. Do not grade by exact wording. A polished reference list without a judgment fails the core task.

`score.py` is an optional scorer for externally supplied source-backed cases and matter runs:

```sh
python3 evals/score.py --case /private/case.json --run /private/matter
```

A case uses `id`, `set` (lite/deep/draft/oa), `input`, and `truth`. Source-backed `truth.references`, `truth.applied` and `truth.examiner_cited` are real identifiers, with provenance and date/scope checks performed by the evaluator. Lite can provide `truth.verdict`; draft can supply `truth.expect` mechanics. Unchecked references/quotes are reported separately, never counted as verified zero fabrication. The scorer measures selected mechanics and recall, not the correctness of legal reasoning.

## Public-data evaluation still to run

Use 15–30 complete public prosecution families: exact claims before rejection, actual rejection, applicant response/amendment and subsequent action. Blind later outcomes, split by family/time, and manually adjudicate reasoning. A rejection is not an infallible truth label; eventual allowance does not prove the original claim was patentable. Allowed-only samples and correlations are not causal strategy evidence.

Public sources and access limits: [examiner review](../references/examiner-review.md). No full public-family benchmark or cross-model comparison has been run. Offline unit tests in `tests/` exercise synthetic mechanics and public-document parsing. Behavioral forward tests complement those tests without establishing real-world accuracy.
