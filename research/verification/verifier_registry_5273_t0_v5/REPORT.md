# T0 v5 result

Disposition: **PASS_HOST_CONSTRUCTION_ONLY** for the frozen precedence corpus.

- Pre-run construction: v5 tests pass 9/9. The parent #5268 IR tests pass 5/5 when invoked from their own directory.
- Preserved setup errors: the first RED harness reached a missing-function `AttributeError`; the test was tightened to assert the absent API and then produced the intended RED failure. One parent-test invocation from the v5 directory failed during module discovery; the correct parent-directory invocation passed 5/5. Neither was a frozen runner invocation.
- After freeze commit `8042ea6e757b90cb0ab74c530ed3eff6db8c68b4`, latest main still matched frozen base `a1d0d0290b8619902d34b13d9e536c4bde063f74` and all source hashes matched. Post-freeze tests: 9/9.
- One runner invocation produced 7 rows, `dispatch_count=0`, and `PASS_HOST_CONSTRUCTION_ONLY`. A separate raw-only audit process independently recomputed all 7 rows and returned the same disposition.
- Raw SHA-256: `6a38ae5862301056fcb5aee48686ff15029851a897465316fd869322e182b943`. Audit result SHA-256: `357f083f828e7df01d28a6a2e40061dfb329a3fb8d3fcbb6833e28313b3dcb41`. Freeze SHA-256: `3bf722e9afeca3323b6e8f852170f9b879cda52117ca631ca8ab226f37fb50cd`.
- Synthetic cost/budget fixture values use the same arbitrary units. No deadline clock behavior or measured latency is asserted.
- Docker/OrbStack invocation count: 0. `STOP_NO_EXACT_RESOURCE_LEASE` per #5085; no CLI inventory was attempted.
- This successor does not complete #5273's broad heterogeneous registry question. V1–v4 stay unchanged; this result should be integrated/reviewed separately.

- Trigger: the v4 post-submit boundary probe found a decision disagreement for an infeasible deadline combined with unavailable resources.
- V5 preserves v4 byte-for-byte and isolates that precedence case under a fresh frozen corpus. Cost/budget values are synthetic same-unit values, not measured latency.
- Container gate: `STOP_NO_EXACT_RESOURCE_LEASE` per #5085. Docker/OrbStack invocation count is 0; no CLI inventory was attempted.
- #5273's full heterogeneous registry question remains broader than this successor.
