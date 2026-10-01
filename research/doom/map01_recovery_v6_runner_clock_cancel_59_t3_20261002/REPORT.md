# T3 execution record — STOP (freeze-order violation)

Allocation: `MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3-20261002-01` (Issue #6242)

## Decision

**STOP — candidate execution occurred before the candidate and independent auditor hashes were recorded on the issue.** The candidate was run once and is preserved as raw, non-formal evidence. It is not a pass, does not satisfy the allocation's acceptance gates, and will not be rerun or retroactively promoted. The next attempt requires a successor allocation with pre-registered hashes and a fresh independent auditor.

## Scope and environment

The harness loaded the exact v6 `_run_arm`, executor-v10, and Lease source Git objects identified below, with a fake v5 base/JsonSession and cooperative mock backend. No game, production control, or live allocation was used. Docker was not used: the shared Docker slot had no recorded owner release and the Docker Desktop service was observed stopped during intake. No attempt was made to start or alter it. This is host-CPU mock evidence only.

## Preserved observations (not acceptance results)

The single candidate invocation completed both cases:

| Case | Timer-to-clock return | Clock return to cancel | Outcome |
|---|---:|---:|---|
| A, 400 ms clock delay / 2 s lease | about 415.837 ms | about 0.111 ms | verified mock release; terminal status `completed` |
| B, 1600 ms clock delay / 1.5 s lease | lease release about 706.2 ms before clock return | cancel unmatched after expiry | verified mock release; terminal status `expired` |

These values are descriptive only. The ordering protocol violation invalidates formal interpretation regardless of the observed values. Exact monotonic timestamps, event rows, and runner summaries are in `raw_trace.json`.

A later read-only arithmetic check of the preserved JSON recomputed A timer→clock as 415.837 ms and clock→cancel as 0.111 ms, and B release→clock as 706.169 ms. This corrects the rounded A value in the initial report; it is a posthoc consistency check, not the preregistered independent audit.

Construction-only smoke passed before the candidate: exact `_run_arm` reached verified release and cancel observation, with release about 15.7 ms after the 30 ms timer. The initial smoke attempt failed before execution due to a harness instrumentation issue (timer import overwritten), which was corrected before the successful smoke and before the candidate.

## Frozen source identities

Base commit: `2240189b46c5f393bb7b1d5080e8eace748b0251`

| Source | Git blob | SHA-256 |
|---|---|---|
| v6 runner | `10344582ffa2ce339bc48dd8d680512a71f4eddc` | `9790becf98104b3a956c73bee945266a8517e41c2396c1a8b29c924e14d26012` |
| executor-v10 | `e0a31884307eeac405094a624e3a63222acc656f` | `e55f82e6f15c39914a4213873d39386205a792c98b54d0cf54be0812c69ecb2e` |
| Lease | `b9dac6bb4063928354733d79bf371909a288a3d1` | `e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f` |

The construction smoke and candidate used the same uncommitted runner script; the candidate/auditor freeze prerequisite was not completed beforehand. `raw_trace.json` is retained without alteration. No independent audit pass is claimed.

## Boundaries

No statement about full runner integration, transport behavior, real input devices, held-input occupancy outside the mock backend, gameplay, MAP01, production safety, or Docker/container reproducibility follows from this record. No roadmap completion is claimed.
