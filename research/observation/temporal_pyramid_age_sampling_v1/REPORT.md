# Temporal frame pyramid age-target sampling — Rung 0 result

Task `TEMPORAL-PYRAMID-AGE-SAMPLING-20260917-001`, Issue #752, child of #746.

## Decision

**`PASS_AGE_TARGETED_TEMPORAL_SAMPLING_SCOPED`**.

This is model-free representation evidence. The same six source frames/budget/role semantics were compared under two selection policies only: fixed frame-index offsets `[0,1,2,4,8,16]` versus target ages `[0,16.666667,33.333333,66.666667,133.333333,266.666667] ms` with nearest-unused timestamp selection.

Formal execution was one invocation, 20 first rows, reruns 0.

## Timing error

| trace | INDEX_LOG sum abs age error (ms) | TARGET_AGE_LOG (ms) |
|---|---:|---:|
| regular_60hz | 0.000010 | 0.000010 |
| alternating_jitter | 16.666667 | 16.333333 |
| burst_drop_middle | 56.666676 | 9.999996 |
| late_jitter | 10.666663 | 10.666663 |
| early_jitter | 1.333330 | 1.333330 |
| mixed_jitter_drop | 63.333333 | 19.999999 |


Regular 60 Hz selects identical observation IDs under both policies. Candidate age error is non-worse on every frozen irregular trace and strictly improves **3/5**: alternating jitter, burst-drop-middle, and mixed jitter+drop. The largest discriminators are burst-drop-middle (**56.666676 -> 9.999996 ms**) and mixed jitter+drop (**63.333333 -> 19.999999 ms**).

All valid outputs contain exactly six unique source observations, newest/current first, monotonically increasing age, exact source ID/timestamp/hash/rect preservation, exact byte accounting, and no historical frame grants current authority. Both insufficient-history rows fail closed, and all six malformed policy rows are rejected before sampling.

## Integrity

Formal result: 113,307 bytes, SHA-256 `02930208f703b3b0e0cd1ca67f5b334863ca9492fb8282352a6fb51afe439a18`. Frozen audit errors `[]`; audit SHA-256 `ab9c6eb0c56b231f13ccf0d2e8229e0c5f37d5994d36b60a506a3f5342ead10e`. Postformal source rehash matches **10/10** frozen source files. Actual formal evidence corruptions are rejected **8/8**. Frozen sampler/audit tests re-pass after measurement.

## Interpretation / boundary

This establishes only that target-age selection better preserves an authored logarithmic time axis under these deterministic cadence disturbances while preserving provenance and historical/current roles. It does **not** show that the temporal pyramid improves motion prediction, model actions, tokens, latency, or task success; it does not establish that these ages are optimal or that the synthetic cadence distribution matches a real watcher. A separate Rung 1 should compare prediction with identical current frame and equal history-frame count before any action/control claim.
