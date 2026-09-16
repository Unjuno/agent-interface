# Temporal pyramid prediction-transfer — retained HOLD

Task `TEMPORAL-PYRAMID-PREDICTION-TRANSFER-20260917-002`, Issue #766, direct successor to #752/#746.

## Decision

**`HOLD_NO_PREDICTION_TRANSFER`**.

The formal block ran exactly once (24 rows; reruns 0). The candidate target-age sampler improved all four smooth irregular prediction discriminators, but the preregistered constant-velocity jitter control required both timestamp-aware predictions to be effectively exact at `<=1e-8 px`. Integer-nanosecond timestamp rounding left residual errors of about `3.15e-8 px` (INDEX_LOG) and `1.79e-8 px` (TARGET_AGE_LOG), so the frozen control gate failed. The threshold is not relaxed post-result; therefore this block remains HOLD rather than PASS.

## Prediction error at current + 50 ms

| case | INDEX_LOG abs error px | TARGET_AGE_LOG abs error px | candidate delta px |
|---|---:|---:|---:|
| static_regular | 0 | 0 | 0 |
| constant_velocity_regular | 1.88035187421e-09 | 1.88035187421e-09 | 0 |
| constant_velocity_jitter | 3.14760768561e-08 | 1.79050800853e-08 | -1.35709967708e-08 |
| constant_accel_jitter | 5.12966935931 | 4.50167227635 | -0.627997082961 |
| constant_accel_drop | 4.15639226383 | 3.62675846474 | -0.529633799083 |
| smooth_turn_mixed | 3.6322244293 | 3.11262100004 | -0.519603429265 |
| recent_accel_mixed | 2.81671754598 | 2.73296631115 | -0.0837512348369 |
| abrupt_reversal | 8.06594841542 | 7.65822070328 | -0.407727712144 |

- Smooth discriminator candidate improvement: **4/4** (`constant_accel_jitter`, `constant_accel_drop`, `smooth_turn_mixed`, `recent_accel_mixed`).
- Abrupt-reversal candidate did not incur the frozen >1 px penalty; it improved by about **0.408 px** in this block.
- Static control is exact in both arms. Regular constant-velocity arms are equal. Jittered constant-velocity errors are numerically tiny but exceed the frozen `1e-8 px` exactness tolerance.

## Allocation discipline

Allocation 001 is retained separately as `STOPPED_CONSTRUCTION_LEAK_FORMAL_CASES`: pre-freeze audit testing accidentally invoked the planned formal generator in memory, so those outcomes were disqualified and never reused. Allocation 002 used a fresh deterministic SHA-derived parameterization, source-first freeze, and construction tests that never called its formal generator. Formal 002 was invoked once only after freeze.

## Integrity

- formal raw SHA-256 `45d28ccd6cb1f43723c5e19b621698ab4d3f7e93e44da382ac0a7ee576337f95`
- frozen audit SHA-256 `6a253622aa632260c365f46d6c6068acc37ed376e108971fadc6ecb89afd8da0`
- postformal frozen-source rehash: **10/10 exact**
- postformal tests: **11/11 PASS**
- actual formal-result corruptions rejected: **8/8**

## Boundary

This does not establish frontier-model prediction benefit, model-visible token/latency savings, real watcher cadence distribution, or action-selection improvement. The posthoc diagnosis suggests the only frozen gate failure is numerical timestamp quantization rather than a substantive motion-prediction regression, but that diagnosis cannot upgrade the preregistered HOLD. A successor should isolate numeric timestamp representation/tolerance independently rather than silently relaxing this block, or proceed to a separately preregistered model Rung 1 only if justified by evidence outside this failed gate.
