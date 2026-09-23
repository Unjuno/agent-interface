# State/event split under planner backpressure — retained container evidence

Task: `EVENT-STATE-SPLIT-20260917-001`

Decision: **`PASS_SPLIT_STATE_EVENT_RETENTION_SCOPED`**

This is the minimal first rung derived from Issues #14/#43/#6/#5: ordinary state is replaceable; authored critical transitions are not. Priority scheduling, batching, ACK/resolution, event backlog capacity, GUI/model/game execution, and planner-token claims are deliberately outside this allocation.

## First formal outcome

Exact frozen source was executed once in an isolated container after construction tests passed 7/7.

- `py_compile`: PASS
- deterministic unit tests: **7/7 PASS**
- formal runner invocations: **1**
- formal reruns: **0**
- `verify.py`: **PASS_VERIFY**
- post-result source rehash: **6/6 PASS**

## Result

| Case | all-record reference | naive latest-only | split state/event |
|---|---:|---:|---:|
| progress storm | 100 visible records | 1 final state | **1 final state** |
| transient focus | 30 records / 2 events | 1 final state / **0 events** | 1 final state / **2 events** |
| lease expiry + release | 10 records / 2 events | 1 final state / **0 events** | 1 final state / **2 events** |
| target lost + terminal | 9 records / 2 events | 1 final state / **0 events** | 1 final state / **2 events** |
| cross-session storm | 110 records / 1 event | 2 final states / **0 events** | 2 final states / **1 event** |

Across the authored critical-event cases, `naive_latest_only` loses **7/7** critical events because later ordinary state replaces them. `split_state_event` retains **7/7** with exact event/session identity and order while preserving the exact newest state for each session. In the state-only storm, it collapses 100 ordinary records to one latest state.

The cross-session case retains A's `FOCUS_LOST` while B produces 100 state updates; A/B latest state remains independently scoped.

## Interpretation

Latest-only replacement is safe for the authored replaceable state records in this fixture but is not a sufficient event-retention policy. The minimal invariant is two channels with distinct semantics:

- replaceable latest state per session;
- ordered retained critical events.

This does **not** prove that the event channel is bounded while a planner is absent indefinitely. It also does not establish planner-boundary, latency, token, or model-attention savings. The next mechanism, only if demanded by an integrated/live failure, is explicit event backlog/ACK/capacity semantics; priority/coalescing/batching should remain separate variables.

## Integrity

Frozen source SHA-256 values are in `source_sha256.txt`. The full deterministic evidence archive contains source, cases, tests, plan, freeze, environment, formal log, result, verifier output and this report. No shared runtime or workflow files are modified by publication.
