# #3270 scorer jitter replay evidence

Status: HOLD_CI_RUNNER_UNAVAILABLE

## H/T/D/C/U

- H: The v7 pair-02 COAST_CONTROL missed period is a real scheduler-lateness observation, not a missing terminal/event record.
- T: Replay the retained timing rows in a container, preserving the adapter policy: emit one current sample, count overdue periods, and never fabricate catch-up samples.
- D: Retain the exact observed schedule/start rows, container command, output, and independent CI disposition.
- C: PASS only for the deterministic replay gate when skipped periods are exactly [0, 0, 1, 0, 0] over the five retained rows and sample cardinality is unchanged. This is not an efficacy gate.
- U: A fresh MAP01 allocation is not authorized until the replay gate and CI plumbing are complete.

## Retained observation

From v7 artifact 10591929720, pair-02/coast_control:

- 35 Hz scorer, 138 samples
- maximum interval 59.510392 ms
- exactly one missed_sample_periods
- localized row: scheduled 208074242800, started 208105240031, lateness 30,997,231 ns
- neighboring rows resume at approximately 28.57 ms

## Container replay

Image: python:3.12-alpine

The replay used period 28,571,429 ns and the five retained schedule/start pairs.

Output:

OBSTAC_REPLAY_GATE PASS [0, 0, 1, 0, 0] 5

Interpretation: the retained pattern is reproduced deterministically; one overdue period is accounted for and no synthetic sample is added.

## CI disposition

- PR #3288 repaired workflow run 35471857847, job 105974123511: queued
- Manual isolated run 35471911447, job 105974278434: queued
- Old blobless sparse-checkout runs are retained but not reused or rerun.

The CI state is an infrastructure HOLD, not a semantic failure and not a MAP01 efficacy result.
