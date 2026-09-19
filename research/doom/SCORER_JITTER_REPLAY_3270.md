# #3270 scorer jitter replay evidence

Status: HOLD_CI_RUNNER_UNAVAILABLE

## H/T/D/C/U

- H: v7 pair-02 COAST_CONTROL's missed period is scheduler lateness, not missing terminal/event data.
- T: Replay retained schedule/start timing in a pinned container using the production policy: emit one current sample, count overdue periods, never fabricate catch-up samples.
- D: Preserve exact rows, container identity, output, source/result references, and CI disposition.
- C: Deterministic replay PASS iff skipped periods are [0, 0, 1, 0, 0] over five retained rows and sample cardinality is unchanged. This is not an efficacy gate.
- U: Do not run a fresh MAP01 allocation until replay and CI plumbing are complete.

## Retained v7 observation

Artifact 10591929720, pair-02/coast_control:

- 35 Hz, 138 samples
- maximum interval 59.510392 ms
- one missed sample period
- localized row: scheduled 208074242800, started 208105240031, lateness 30,997,231 ns
- adjacent rows return to approximately 28.57 ms

## Container replay

Image: python:3.12-alpine

Output:

OBSTAC_REPLAY_GATE PASS [0, 0, 1, 0, 0] 5

Boundary replay also passed:

OBSTAC_SCHEDULER_BOUNDARY PASS [('on-time', 0), ('one-period-overdue', 1), ('two-period-overdue', 2), ('boundary-before-next', 0)]

## CI disposition

- PR #3288 repaired workflow: merged as 860e3ec, but its checks were queued at merge.
- Manual isolated run 35471911447, job 105974278434: queued.
- Old blobless sparse-checkout runs are historical and were not rerun.

This is a scoped replay result plus infrastructure HOLD. It is not a MAP01 efficacy PASS.
