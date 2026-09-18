# Temporal sampling prediction error envelope — Issue #1497

Task: `TEMPORAL-SAMPLING-PREDICTION-ERROR-ENVELOPE-20260918-001`

H: with INDEX_LOG and TARGET_AGE_LOG frozen, a timestamp-only worst-case bound for the shared OLS linear predictor is exact under a declared constant-acceleration and bounded-observation-error class. MIN_BOUND may choose the lower guarantee without claiming lower realized error.

T: stdlib-only. Current=0, horizon=100ms, six samples. INDEX [0,1,2,4,8,16]. TARGET ages [0,16.666667,33.333333,66.666667,133.333333,266.666667]ms. A_max levels {0,200,500,1000,2000}px/s^2; q_max=0.5px. Construction checks exhaustive tightness. Formal is 120,000 supported +6,000 affine-clean +10,000 unsupported controls, one invocation.

D: no candidate/oracle mismatch or supported bound escape; adversarial construction tight; MIN_BOUND guarantee <= both fixed guarantees; each sampler selected >=10,000 formal supported rows; malformed/unsupported/provenance violations fail closed; integrity exact.

C: this is an OLS/constant-acceleration fixture, not a model or real motion guarantee. Lower worst-case bound need not mean lower realized error.

U: no model/GUI/action/token/latency/human-tempo/production claim. Do not tune age targets or rerun consumed parent allocations.
