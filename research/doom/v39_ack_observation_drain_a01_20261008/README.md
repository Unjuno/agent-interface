# V39 accepted-ACK typed-observation retention A01

## Question and scope

This source repair addresses a concrete queue-dispatch gap in the current V39 action path: `execute_segment` waits for an accepted/rejected acknowledgement without an observation monitor. A typed observation consumed by that wait was removed from the queue and therefore was unavailable to the running-action guard during the subsequent monitored terminal wait.

This is a deterministic unit-level source repair. It does not claim that a live executor accepted input before a given observation, measure the frequency or duration of the window, validate HUD extraction or cadence, or establish physical key release, recovery quality, or task success.

## H/T/D/C/U

**H — Hypothesis:** If the acceptance wait consumes a typed health/ammo row before the matching accepted acknowledgement, retaining that row and replaying it through the admitted action's running monitor will preserve a hard invalidation for the existing cancellation/release/terminal-closure path.

**T — Test:** The focused regression queues a typed health-70 observation followed by acceptance, extracts the production `wait` and paired monitor from the controller source, and asserts that the row is buffered and evaluated as `health:below_hard_minimum`. A source-order check verifies that `execute_segment` admits before replay and replays before entering the monitored terminal wait. The focused suite is run under regular and optimized Python; production/test files are syntax-compiled and `git diff --check` is run.

**D — Decision:** PASS for the demonstrated dispatch-retention property when the focused regression passes in both interpreter modes and the execution ordering assertions hold. HOLD for live timing, executor input onset, physical release, and integrated task outcomes.

**C — Competing explanation:** A real executor/backend may serialize observation and acceptance differently, so the reproduced synthetic queue order may be rare or unreachable on a particular deployment. Even when reachable, a late observation can reflect a state change after some input has already begun; this repair can only trigger the existing invalidation path once the accepted program is recorded.

**U — Uncertainty:** No live executor, Doom process, GUI/input backend, or formal allocation was used. The test proves source-slice behavior for the constructed rows and guard contract; it does not prove production scheduling or physical release. Typed rows are forwarded to the action guard here; this change does not make typed-only rows update the legacy `latest` planning snapshot.

## Result and provenance

- Base: `6da5dc940fdb97866cfb900ca747edb8c94b2790` (`origin/main` at branch creation and final local comparison).
- Implementation commit: `ccd6d72cfd49242667eff6a32a6396c1eba9c6f0`.
- Regression: `research/doom/test_map01_v39_pair_wait_dispatch.py`.
- Runtime path: `research/doom/map01_overlap_controller_v39.py`.
- Pull request: [#8441](https://github.com/Unjuno/agent-interface/pull/8441), open and not merged at record creation.
- Local result: 3 focused tests passed in normal Python and 3 passed under `-O`; `py_compile` and `git diff --check` passed.
- Status: scoped construction/repair PASS; live/integrated behavior HOLD. No formal allocation was used or retried.

## Applicability correction (2026-10-08)

The typed-before-accepted queue order used by the original helper regression is not reachable on the audited V39 session routes, so the helper-level PASS does not establish a production observation-loss defect.

The current-main route check covers both the default `session_map01_v12.py` path and the opt-in measurement `session_map01_v15.py` wrapper, including its release-ordered executor and release-batch backend. V12's executor emits the accepted row through the session's shared emitter before starting its worker. The v15 executor delegates to that v12 submit path before starting its release watcher. The v15 release-batch and typed-release backend wrappers delegate synchronously into the same typed snapshot path without creating a separate observation worker. The session emitter prints and flushes each JSON line under a lock. Active typed observations are emitted synchronously from the backend snapshot called during worker execution. The controller's single stdout reader decodes and enqueues each line before reading the next. Thus the accepted row is enqueued before any typed observation produced by that accepted program on these pinned routes.

A source-order regression now checks the current repository files for both routes and the shared FIFO path. It passes under normal and optimized Python. This is static source-order evidence; it does not establish live timing, HUD correctness, physical release, or task outcome. The retained construction still demonstrates how buffering would handle an artificial pre-ACK row. It does not justify that buffer in the current V39 runtime. [PR #8451](https://github.com/Unjuno/agent-interface/pull/8451) proposes reverting the unnecessary runtime and helper-test additions while retaining this evidence and the source-order regression.
