# Temporal OLS timestamp-origin conditioning v1

Decision: **PASS_ORIGIN_SHIFTED_TIMESTAMP_CONDITIONING_SCOPED**.

## Question
The predecessor #779 retained `HOLD_NO_PREDICTION_TRANSFER` because a jittered constant-velocity exactness control exceeded its frozen `1e-8 px` tolerance by only a few `1e-8 px`. This experiment changes only timestamp numeric representation before the same ordinary least-squares constant-velocity fit.

- baseline: convert absolute integer nanoseconds to float seconds, then fit;
- candidate: subtract the newest timestamp in exact integer nanoseconds first, then convert deltas to float seconds and fit.

No threshold, sample set, predictor family, horizon or weighting differs.

## First formal outcome
One formal invocation, **32 first rows**, reruns/replacements **0**.

- candidate max absolute error: **2.2204460492503131e-16 px** (gate <=1e-10);
- candidate origin spread: positive=0.0, negative=0.0, slow=0.0 px (gate <=1e-12);
- baseline high-origin max error: positive **3.6334995456854813e-08 px**, negative **1.925029096128128e-07 px**;
- baseline origin spread: positive **5.9604644775390625e-08 px**, negative **1.9250728655606508e-07 px**;
- static trace exact under both policies;
- all frozen gates true; audit errors `[]`.

This reproduces the predecessor's numerical scale without relaxing its control tolerance: absolute timestamp conversion makes an otherwise identical relative motion prediction depend on timestamp origin, while exact integer origin subtraction removes that dependence in this fixture.

## Integrity
Prefreeze static tests 2/2 and `py_compile` passed. Remote source freeze was read back **9/9 byte-exact** before formal. Postformal source SHA-256 recheck is exact for all frozen scientific files. Four copied-evidence corruptions are rejected 4/4. Formal result SHA-256 `a93fdb3b25aa060dd5cafb65aed3b6e21047726ccc7854f5d2168bcc5b4a1a5c`; audit SHA-256 `0f2b3e8ca99d2eb85a2649890aa068056fd0f7d3f2139f9e95673f641066c4fb`.

Preformal GitHub publication history contains two branch-only routing/noop incidents before the exact freeze ref; formal rows were zero throughout. The scientific freeze used for measurement is the exact nine-file tree at branch commit `36b325e38bc8512efd973735cb25c5f94d74aa1c`.

## Interpretation / limits
This is deterministic Python/IEEE-754 numerical-conditioning evidence only. It supports subtracting a local integer timestamp origin before floating regression. It does **not** establish that constant velocity is a good motion model, repair acceleration/reversal behavior, prove real watcher timestamp distributions, improve model decisions, or authorize action/control.
