# Issue #4889 — finite partial-order replay experiment

## Disposition target and lineage

Successor to #1748 and parent idea #1715. The #1748 total-order theorem and active empirical replay task #2993 remain untouched. This allocation asks whether some order edges can be omitted *inside the exact declared finite reducer* when their event occurrences commute from every reachable state. It does not inspect or replay any real trace.

Intake main: `055468a4831960f5647760d4f25c54923526c5a3`.
Owned branch: `research/replay-partial-order-1748-4889-v1`.
Owned path: `research/analysis/partial_order_replay_4889_v1/`.
Allocation: `partial-order-replay-4889-20260927-01`.

## H / T / D / C / U

**H.** If two event definitions commute on every reachable state (same resulting state and same typed output per stable event occurrence), then preserving the original order only for dependent occurrence pairs is sufficient for every topological ordering of that dependency DAG to reproduce the full-order final projection and per-event outputs. The test is conservative: it does not exploit state-local commutativity.

**T.** The standard-library reducer has state `(observation, observation_revision, plan, plan_revision, tool_result, authority_open, authority_generation, logical_time, lease_expiry)`. Typed events are `OBS0`, `OBS1`, `PLAN0`, `PLAN1`, `TOOL0`, `TOOL1`, `OPEN`, `CLOSE`, `TICK`, and `REQUEST`. Values/revisions are bounded and revisions saturate at 2, so the state space is finite. `REQUEST` records ADMITTED only when authority is open and unexpired, the plan is present/current/matches the observation, and the tool result is true; otherwise it records a typed refusal. Every event occurrence has a stable identity equal to its original word position; output order is not observable, but the per-occurrence output map is.

The candidate independently enumerates all states reachable from the initial state under this alphabet (construction found 2,025), tests all 100 ordered type/payload pairs over all reachable states (202,500 pair-state checks), and enumerates all event words of lengths 0 through 4 (11,111 words). For each word it adds original-order edges for every dependent pair, enumerates every topological linearization, and compares final state and the output map with the full-order reference. A negative control removes the OPEN-before-CLOSE edge and requires a divergent linearization. One source-frozen formal candidate invocation is followed by a separate raw-only auditor which re-derives the state universe, commutativity matrix, all legal linearizations, aggregates, and eight copied-record corruption controls.

**D.** `PASS_PARTIAL_ORDER_REPLAY_SCOPED` iff every legal linearization matches, at least one word strictly reduces order edges, the dependent-edge omission control diverges, all source/denominator/hash checks pass, independent audit errors are empty, and all eight effective controls reject. Any mismatch is `FAIL_PARTIAL_ORDER_REPLAY_UNSOUND`; missing reduction or a missing negative discriminator is HOLD; unavailable source/image/audit is STOP. One formal invocation; retries, replacements and post-result tuning are zero.

**C.** Event operations are deterministic and completely described by the reducer; event identities are stable; output order itself is not an observable. Total pairwise independence is deliberately stronger than necessary. Omitting hidden state, event types, side effects or observable ordering could make a real-world commutativity declaration unsound.

**U.** No real retained trace, event store, GUI, model/provider, GPU, concurrent execution, hidden OS scheduling, wall-clock behavior, external process, storage saving, latency, token, production, task, authority or product claim. A PASS cannot weaken ordering in #2993 or a runtime trace without a separate source-bound transfer study.

## Frozen source identities

- `runner.py` SHA-256: `6e80ce bcea36c76427fad6797a302a2672e965bca280abd4166a3d13872f275c` (remove the display space: `6e80cebcea36c76427fad6797a302a2672e965bca280abd4166a3d13872f275c`).
- `audit.py` SHA-256: `a3b96773ebea184eb7741e467662203a9eeee7feea1186127b7c824e40c3c666`.
- Image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64.
- Host: Docker Desktop 29.8.0, Docker Engine 29.8.0, daemon linux/x86_64.
- Formal container bounds: network none, read-only root and source, 0.25 CPU, 384 MiB RAM, 64 PIDs, tmpfs `/tmp`; evidence output mounted writable and isolated. GPU disabled/not requested.

## Construction (excluded from formal allocation)

Before source freeze, a network-disabled read-only Docker smoke checked state closure, symmetry/reflexivity of the independence table, all 100 length-2 event words and the two-order OPEN/CLOSE control. It passed: `CONSTRUCTION_PASS states=2025 pairchecks=202500`, exit 0. Construction used 0.25 CPU/256 MiB and produced no formal result files. No source changes followed the recorded source hashes.

## Reproduction

From a clean output directory, run `python -S -B runner.py` with `OUT=/evidence/formal01`, mounting the frozen source read-only and the evidence root writable. Then run `python -S -B audit.py` with `EVIDENCE=/evidence/formal01`, keeping source read-only. The formal runner is invoked exactly once; the audit is a separate verification pass, not a scientific rerun. Complete exact commands, stdout/stderr, exit codes, file hashes and outputs are retained alongside this plan.

