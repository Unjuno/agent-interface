# Post-merge weight-validation follow-up

The original T0 sources and `formal_01/` results remain unchanged. This follow-up keeps the NaN boundary defect reproducible and provides a separately named hardened candidate and independent input validator.

## Reproduction and repair

The original `candidate.evaluate` accepts a non-finite weight because it checks only numeric type and `x < 0`; IEEE NaN satisfies neither rejection condition, and `abs(sum(weights) - 1) > tolerance` is also false when the sum is NaN. It returns `NO_FEASIBLE_ROUTE`. The original auditor repeats this arithmetic and returns `PASS_METHOD_SCOPED` for the same in-memory mutated case.

`candidate_hardened.py` rejects non-finite, negative, boolean, malformed, unnormalized, and score-overflowing weight vectors as `HOLD_INPUT_INVALID`. It handles arbitrary-size integers without converting them unsafely through `math.isfinite`, and rejects non-object preference inputs before calling `.get`. `auditor_hardened.py` independently checks the weight vector shape, finite values, nonnegativity, and normalized sum. Direct execution writes only to `followup_01/` and records `candidate_hardened.py` as the command; it never targets the frozen `formal_01/` directory. Neither file is used to regenerate or overwrite the original raw evidence.

## Verification

Six follow-up tests pass: exact NaN reproduction against both original paths; fail-closed checks for NaN/infinities/negative/boolean weights; oversized-integer and non-object-input rejection; overflowing-total and finite-outcome/normalized-weight score-overflow cases, plus a mixed huge-integer/float weight-sum overflow case, and subprocess verification that direct execution writes only `followup_01/` with the correct command receipt. The two existing focused method tests also pass. The historical evidence-byte test fails on this Windows checkout because Git's working-tree conversion changes `formal_01/RAW.json` from 1,895 LF bytes to 2,012 CRLF bytes; the committed blob still hashes to the frozen SHA-256 `9d1648df8fe6a2e5a083984b253cd431a01690453e0bbff085062b62c4033a69`. The Linux CI check previously passed against the frozen bytes. This line-ending issue does not affect the new in-memory validation tests.
