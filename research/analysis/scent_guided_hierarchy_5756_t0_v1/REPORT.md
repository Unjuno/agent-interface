# T0 result — Issue #5756

**Disposition: `PASS_METHOD_SCOPED`; H remains `NOT_EVALUATED`.**

The frozen matrix completed 25/25 fixture-policy rows. The independent raw-only audit exited 0, replayed all 25 rows, confirmed identical visible observations for matching node+epoch, and found zero forbidden effects. The four preregistered mutation controls were each rejected by the independent auditor in the pre-formal 8/8 construction suite.

| Fixture | Eligible-arm outcome | Cost observation (API calls) |
|---|---|---|
| Misleading cue + epoch invalidation | scent, exhaustive, strongest-cue and FIFO tree all found target safely | all four: 9; no scent saving observed |
| No target | no arm claimed success | 1–5; explicit negative control |
| No safe path | no arm claimed success; unsafe edge refused | all five: 2; forbidden effects 0 |
| Budget exhaustion | the four eligible navigation arms did not observe target within 12 calls | all four: 12; direct-search arm N/A |
| Direct search exposed | all five found target safely | direct/exhaustive/tree: 3; scent/strongest-cue: 11 |

The direct-search fixture is a useful counterexample: hierarchical cue/strongest-cue exploration was costlier than the visible direct shortcut. On the deliberately ambiguous positive fixture, all four safe search policies had the same call count. These are hand-authored deterministic cases, not a sampled GUI benchmark; they neither establish a general cost advantage nor meet the adequacy bar for `H_FAIL_SCOPED`. Do not promote this method PASS to live GUI, model, task-effect, GPU, or product evidence.

## Reproduction

- Frozen source/spec: see `FREEZE.json`; base main `82a494a6666bdab92a399cf54ad31e1d42ab204d`.
- Runtime: CPython 3.11.9, Windows host, CPU-only. No container, GPU/CUDA, model, GUI, network, or external effect was used. A shared container lane was not presumed available or used.
- Candidate: `python -B runner.py --output outputs/raw_results.json` — one invocation, exit 0, 25 rows.
- Independent audit: `python -B audit.py outputs/raw_results.json outputs/independent_audit.json` — separate process, one invocation, exit 0, `PASS_METHOD_SCOPED`.
- Raw output SHA-256: `2190C0D2EDEB2B354C265B64F3FB687B7AD7FF0A9A2193CA223294F7C27AD050`.
- Audit output SHA-256: `06B6F02E73D44E9E871ED91C55EBB2C70FB06CB4AEF0F0886C724C6017C67B5B`.

