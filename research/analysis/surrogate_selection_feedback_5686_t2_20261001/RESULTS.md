# T2 formal result: metric-guided selection feedback

## Verdict

`PASS_SELECTION_FEEDBACK_GATE_SCOPED` for the preregistered finite synthetic gate only. This is not empirical validation of an agent-interface metric or a claim about a deployed policy.

## Allocation and execution

- Allocation: `SURROGATE-SELECTION-5686-T2-GHA-20261001-02`
- Workflow: [run 36810159646](https://github.com/Unjuno/agent-interface/actions/runs/36810159646)
- Frozen base: `5ff239141f49c1603c0f6b078268f4a2f6e082df`; both jobs verified it as an ancestor and verified frozen sources.
- Candidate and independent raw-only auditor each ran once, in separate GitHub-hosted Docker jobs; both exited 0. The shared local OrbStack lane was unavailable under Obstac, so no shared Docker state was inspected or changed.
- Image: `python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`, linux/amd64; observed image ID `sha256:febd0be41adb897a0ab8f1f1c693d8912669ea60c4940e076e9946b60e210ef0`.
- Candidate emitted 192 attempts across four worlds and four fixed strata, with selection and disjoint sealed splits. All opportunities, including missing observations and safety failures, were retained and scored on the fixed sealed population.

## Outcomes

| World | Result |
|---|---|
| `stable` | `SCOPED_SELECTION_CONCORDANCE`; selected balanced policy, endpoint balanced, sealed utility 9, coverage 1, safety failures 0 |
| `selection_overfit` | `HOLD_METRIC_SELECTION_EFFECT_NOT_REPLICATED`; metric selected lucky policy, endpoint balanced, sealed utility 8, coverage 1, safety failures 0 |
| `observation_shift` | `REJECT_SELECTION_COVERAGE_OR_ENDPOINT_REGRESSION`; metric selected metric_drop, sealed winner coverage 0.25 and utility 2.25, safety failures 0 |
| `safety_regression` | `REJECT_NONCOMPENSABLE_SAFETY_REGRESSION`; metric selected reckless, sealed utility 10 but hard safety failures 4 |

The authored controls distinguish selection-only overfit from observation-availability loss, and enforce safety independently of utility.

## Integrity and local verification

- Formal candidate JSONL SHA-256: `655da10fe994db0ed8e120eed69d29c64810393972e53a0578323eee95d26573`.
- Formal audit JSON SHA-256: `bce3a67d70a2ea4dc73a26eadc61c827d8f15e82cd0fae48ca0daec1873cefd5`.
- A fresh local raw-only audit over the formal JSONL reproduced the formal audit JSON byte-for-byte.
- Local checks: 6/6 unit tests; Python compile; JSON/YAML validation; analysis index; frozen-source hashes; base ancestry and diff checks all passed. Local development is not counted as formal Docker evidence.
- Complete formal raw outputs, start gates, container logs, image-pull logs, execution records and container IDs are retained beside this report under `raw/formal/allocation-02/`.
- Predecessor allocation -01 remains separately preserved under `raw/formal/allocation-01/`. It is `NOT_EVALUATED`: the candidate ran, but an artifact-path error prevented the auditor container from launching. It is not a scientific counter-result and was not reused as -02 input.

## Limits and next evidence

All worlds and endpoint utilities are authored synthetic finite controls. There are no empirical task/model/GUI observations, randomized policy effects, causal estimates, or transportability evidence. In particular, the concordant case does not establish predictive validity of a surrogate. Any real metric promotion requires prospective, independently endpoint-scored, held-out task/route evidence with missingness and safety handled as preregistered here.
