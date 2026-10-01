# Temporal pyramid local predictor — retained HOLD

Task `TEMPORAL-PYRAMID-LOCAL-PREDICTOR-20260917-001`, Issue #808.

## Decision

**`HOLD_NO_PREDICTION_GAIN`**.

This is a model-free pre-model discriminator. The underlying trace, current observation, six-frame budget, timestamp-aware OLS predictor and 100 ms horizon were fixed; only sampling policy changed (`INDEX_LOG` vs #752 `TARGET_AGE_LOG`). Formal execution was one 48-row invocation, reruns 0.

## Main result

Across the 12 preregistered smooth/constant irregular strata, target-age sampling strictly improved **7/12**, regressed **2/12**, and tied the remainder. Aggregate median absolute prediction error improved from **2.076085px** to **1.866089px**, but the frozen non-worse-all-strata gate failed.

Regressions:

- `constant_quantized + burst_drop_middle`: **0.066810px -> 0.130000px**.
- `mild_accel + alternating_jitter`: **5.026880px -> 5.121275px**.

The recent-direction-reversal hazard did not show systematic candidate worsening under the frozen >1px / >=3-of-4 rule, but both policies remained poor (~19–20px), showing that sparse historical context can remain stale for a simple linear predictor.

Therefore the #752 representation timing improvement does **not** monotonically translate into local short-horizon prediction improvement. This result does not justify proceeding directly to a frontier-model temporal-pyramid comparison on the assumption that better age spacing is sufficient.

## Integrity and audit boundary

Frozen audit on the untouched first outcome returned errors `[]`; source rehash matched **8/8** frozen science files and postformal tests passed. Formal raw SHA-256 `ab80917b8ce6fdabc9f193408bf611cd88727f85c935185fd22d90a83c2d53e4`.

Postformal corruption testing exposed two frozen-auditor limitations that are retained, not repaired retroactively: missing/duplicate rows can crash the auditor with `KeyError`, and the stored `abs_error_px` field is used by gates but is not independently recomputed. A separate explicitly posthoc verifier recomputes row keys, selected IDs, predictions, ground truth and absolute error and passes the untouched raw while rejecting the nonzero `abs_error_px` corruption. The scientific allocation is not rerun.

## Boundary / next question

Synthetic one-dimensional trajectories, integer-pixel quantization and an OLS constant-velocity predictor only. No frontier-model, image understanding, token/latency, GUI action or task-success claim. The next useful question should focus on **history regime-change handling / recency weighting or an equal-frame-count model comparison only with the stale-history hazard made explicit**, not on further tuning the age targets to rescue this block.
