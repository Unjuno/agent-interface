# Issue #6001 hidden-model-shift canary T0

**Disposition: `PASS_METHOD_SCOPED` for the frozen synthetic API fixture only.** This continues the open [Issue #6001](https://github.com/Unjuno/agent-interface/issues/6001) after the separate shared-workload-interference T0 was merged as [PR #6088](https://github.com/Unjuno/agent-interface/pull/6088). This experiment addresses the core measurement idea: can a fixed non-action deck detect an in-deck behavior shift behind an unchanged model alias, while keeping metadata/schema/context changes and coverage limits distinct?

## H / T / D / C / U

- **H:** A bracketed canary will detect a planted in-deck semantic-output shift under a stable alias before B starts, and will hold a B block that contains a mid-block shift. A clean deck is only `NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED`, never proof of unchanged weights/serving behavior. Schema-only, prompt/context, and exposed-snapshot changes must not be mislabeled as semantic model drift.
- **T:** Frozen no-network mock API, with evaluator-only planted truth separated from candidate observations. Seven scenarios × three policies × 200 trials/group: stationary; hidden in-deck shift between A and B; hidden out-of-deck shift between arms; schema-only break; prompt/context drift with stable model; exposed snapshot change with stable semantics; and in-deck shift halfway through B. Policies are alias-only, exposed-metadata-only, and bracketed-canary. Canary deck has five non-action classes, 20 binary responses/class/trial at before-A, between-arms, and after-B phases. Route A/B outcomes and all four B positions are retained.
- **D:** PASS gates (all true in the independent audit): hidden in-deck between-arm shift → `HOLD_BEHAVIOR_SHIFT_BEFORE_B`; hidden mid-B shift → `HOLD_BLOCK_SPANS_BEHAVIOR_SHIFT`; stationary and out-of-deck clean canaries retain the narrow unverified wording; schema, prompt/context, and visible snapshot controls map to their distinct HOLDs; all route trials remain present; and no policy claims model behavior/identity verified from alias or a clean deck. Raw contains 21 scenario-policy groups, 200 A and 200 B trials/group, 21,000 retained route-row outcomes, and 420,000 bracketed probe attempts (including all five classes and three phases). Audit errors=0; mutation tests=9/9 PASS. A second frozen-source execution is byte-identical (SHA-256 `0cbd75a36215eda262ec1609e25d905d8816e3392e050d210120a6681d688bb6`).
- **C:** This is a controlled discrete fixture, not a real provider. Route order is fixed A→B (so this does not estimate/order-balance serial drift); outputs are seeded Bernoulli draws; the candidate threshold is frozen at a 0.20 canary success-rate decline. The mock separates semantic behavior, metadata, schema and context by construction. The prior PR #6088 separately tested shared-queue probe workload in a simple FCFS fixture; it does not validate this service model.
- **U:** No provider/model/API was contacted. No claim of real-world canary power, false-alarm probability, queue/quota/cache behavior, causal route-effect validity, or model identity. Out-of-deck shifts are intentionally undetectable by this deck; the only safe negative statement is no shift detected within the tested deck. The deterministic route schedule does not test balanced/interleaved order, realistic nondeterminism, multiple simultaneous shifts, provider rate limits, or live model call cost.

## Result detail

The bracketed policy dispositions recomputed from raw were:

| Scenario | Disposition |
|---|---|
| Stationary | `NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED` |
| Hidden in-deck shift between arms | `HOLD_BEHAVIOR_SHIFT_BEFORE_B` |
| Hidden in-deck shift within B | `HOLD_BLOCK_SPANS_BEHAVIOR_SHIFT` |
| Hidden out-of-deck shift | `NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED` |
| Schema-only change | `HOLD_SCHEMA_CHANGE` |
| Prompt/context drift | `HOLD_PROMPT_CONTEXT_DRIFT` |
| Exposed snapshot change, semantics stationary | `HOLD_SNAPSHOT_CHANGED` |

The alias-only and metadata-only controls never claim behavior verified. Their inability to detect the hidden in-deck shift is visible in retained dispositions; metadata-only still detects the explicit schema, context-hash, and snapshot controls.

## Reproduction and provenance

Preparation main: `26f1da8f0a68cb256ea1b3623ef93b2cec4a0ef0`. Protocol and decision gates were frozen in `PROTOCOL.md` and `FREEZE.json` before the official run. The frozen source/image identities and all artifact SHA-256 values are in `SHA256SUMS`.

Executed in OrbStack Docker Engine 29.4.0, Linux ARM64, using `python:3.12-slim` digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, with `--network=none`:

```sh
docker run --rm --pull=missing --network=none \
  -v "$PWD":/work -w /work python:3.12-slim \
  sh -lc 'python simulate.py raw.jsonl && python audit.py raw.jsonl > audit.json && python -m unittest -v test_detection.py'
```

Before the freeze, the first construction invocation raised a Python `TypeError` while summing nested canary arrays and produced no raw output. That construction failure and the corrected pre-freeze construction output are retained as `CONSTRUCTION_FAILURE.md`, `construction_raw.jsonl`, and `construction_audit.json`; the official post-freeze output is separate. The corrected official run and independent audit pass. No formal provider allocation was opened, retried, or consumed. Historical allocation-01/02 mount STOPs on #6001 are unchanged.
