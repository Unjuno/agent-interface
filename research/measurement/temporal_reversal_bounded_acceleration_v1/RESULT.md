# Bounded-acceleration reversal safety result

Decision: **FAIL_BOUNDED_ACCELERATION_SAFETY**.

Formal invocation1, reruns0, 6,000/6,000 rows. A0 exactly reproduced #1319 B1000 at all six ages with wrong-direction0.

Wrong-direction rows: **8**.

- AM1@200: 3/200
- AM2@200: 3/200
- AP2@200: 2/200

Interpretation: a correctly calibrated per-sample localization bound is not sufficient when the estimator assumes constant velocity but the true post-reversal motion has bounded acceleration. The frozen estimator can emit a confident wrong current direction rather than UNKNOWN.

No rerun, retuning, acceleration narrowing, or threshold change was performed after output.

Raw local FORMAL_RESULT.json SHA-256: `28be0f0e95190d5798488047e67faca8e86395356bf9acb43d872d66b46200a8`.
