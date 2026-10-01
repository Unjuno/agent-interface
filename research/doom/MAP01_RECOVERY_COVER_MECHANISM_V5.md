# MAP01 bounded-recovery mechanism v5

Status: **CONSTRUCTION FROZEN AFTER V4 HARNESS FAILURE; FORMAL WORKFLOW NOT YET CREATED.**

Reserved allocation: `map01-recovery-cover-mechanism-live-v5-01`.

## Why v5 exists

V4 passed source closure, global one-shot ownership, dependencies, and every deterministic construction/measurement regression, then entered its first formal block. Run `34980663904` stopped in pair 1 while waiting for a terminal event. The retained raw trace shows that the coast fallback did emit a verified-empty `terminal(status=cancelled)` after the planner timer. The runner had already consumed that terminal while performing an optional wait for `input_released`, because `JsonSession.wait()` discarded every event that did not match its current predicate. The subsequent terminal wait therefore timed out.

This is a harness event-routing failure, not evidence for or against bounded recovery. V4 is consumed and will not be rerun.

## Frozen repair

V5 changes one mechanism in the runner: unmatched session events are queued in a local pending deque and remain available to later waits. No runtime/session/backend source changes. No scientific condition, threshold, fixture, seed, recovery authority, occupancy algorithm, scorer contract, terminal audit, or decision rule changes.

The exact V4 failure order is now a regression: a terminal arriving while an optional `input_released` predicate is pending must remain retrievable by the following terminal predicate.

## H / T / D / C / U

**H.** Under the unchanged V4 condition, source-bound bounded recovery reduces measured input-free planner-wait time while preserving launch, release, scorer, terminal, and negative-outcome gates.

**T.** One new workflow-path-global allocation with the same three counterbalanced pairs and zero model calls. Before formal execution, rerun V4 construction tests, occupancy tests, global-owner tests, terminal-score tests, plus V5 event-preservation regressions.

**D.** Exactly `PASS_MECHANISM_ONLY`, `HOLD`, or `FAIL` under the unchanged V4 thresholds. No post-outcome threshold or condition changes.

**C.** Even with the harness repaired, recovery can remain useless, harmful, immediately cancelled, or measurement-invalid. A PASS remains mechanism-only.

**U.** One fixture, simulated planner delay, sparse useful events, scheduling jitter and interval censoring remain dominant. V5 removes a known event-delivery bug; it does not reduce those scientific uncertainties.
