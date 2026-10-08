# Construction log — Issue #8629 T0 A01

Allocation: `EPISTEMIC-ACTION-8629-T0-A01-20261008`  
Formal candidate/auditor invocations: **0 / 0**. No scientific result exists.

## TDD chronology

1. Wrote two generator-contract tests before the generator: stable seed-bound identifiers, 12 unique cases, blinded inputs without stratum/oracle labels, and held-out surface receipts.
2. The first test invocation exposed a test-module import-path error (2 errors, no assertions reached). Changed the test to use the package-relative import; this was test harness correction, not a product or scientific outcome.
3. With a minimal empty generator stub, both tests failed on the expected assertions (0 instead of 12 cases, and missing case IDs). Implemented the minimal generator; both tests passed under normal and optimized CPython.
4. Added a test requiring a distinct policy-input envelope and separately retained truth data. It first failed because the input/truth envelope was absent, then passed after implementing the envelope.
5. Added reference-policy action-choice tests across all six observable evidence configurations, a no-action control, and a stopping-defect policy. The absent policy module initially caused import errors; after a return-None stub made the tests execute, all policy assertions failed as expected. Minimal selection logic then passed.
6. Added a literal acquisition-response receipt test; it failed on the first implementation's receipt spelling mismatch and passed after correcting the generated receipt identifier.
7. Added candidate action-receipt use and arm-access tests before the runner. Implemented a raw trial output that uses only case input and the assigned prescription; its unit tests pass.
8. Added a 144-row Cartesian-coverage test before `run_trials`; a minimal empty stub failed the expected row-count assertion (0 vs 144), then the full policy × arm × case runner passed.
9. Added planted action-selection, recognition, and evidence-use defects before implementing their signatures. The initial outputs failed on the declared assertions; implementations now preserve distinct observable channels.
10. Added a data-partition test for 48 cases across fixed seeds 17/29/41/53. An empty fixture/oracle stub failed the case-count assertion; the generator now separates candidate inputs (including only a top-level prescribed treatment key) from the oracle map, and duplicate case IDs fail closed.
11. Added a raw-only auditor and four mutation tests. The initial auditor stub failed the expected baseline and corruption assertions. The independent reconstruction then exposed a candidate/auditor disagreement on whether a no-action arm could commit under the stopping-defect policy; corrected the candidate's arm boundary before any formal invocation, and the reconstructed baseline plus all four controls now pass.
12. Added explicit hypothesis gates for recognition, action selection, evidence production/use, stopping-vs-task-success contrast, and zero hard-gate violations. The new gate test first failed because the gate record was absent, then passed after deriving gates from raw reconstructed metrics.
13. Added source-hash and non-overwriting-output tests before implementing their runner helpers; the initial helpers failed both tests, followed by passing SHA-256 preflight and exclusive output reservation.
14. The first direct data-preparation script launch failed because package-relative imports require module context. Added an explicit script-mode import path; fixture and oracle generation then completed (18,591 and 4,024 bytes). This was a construction/setup failure, not a candidate or formal invocation.
15. Main advanced after branch allocation from `8aeca9c` to `3daf9e1` (11 commits ahead). Read the updated current-goal and roadmap; the intervening tree adds #8610 common-cause work plus the analysis index/workflow and does not touch this successor path. The empty research branch was fast-forwarded to current main, and the base SHA in this pre-formal plan/freeze was refreshed before formal launch.
16. Main advanced again to `bd31228` before freeze publication (8 commits since `3daf9e1`): only the analysis index and Issue #8594's additive reverse-stress package changed. No overlap with the #8629 path. Fast-forwarded the empty branch and refreshed the current-main base SHA before formal launch.
17. Latest full construction suite: 17/17 pass under normal CPython and 17/17 under `python -O`.

## Boundary

Deterministic generator, five policy variants, fixture/oracle partition, candidate runner, independent raw-only auditor, mutation tests, and one-shot runner are constructed. The final source/data freeze, remote freeze publication, and formal execution remain pending. Seeds vary case/provenance identities over the same six authored semantic strata; this does not demonstrate broad semantic generalization. Do not promote these construction checks to a method PASS or H result.
