# T0 v5 result

This report is a result ledger. Before the frozen run, it contains only the
discriminator and gate; the disposition will be added after the one-shot runner
and independent raw-only audit complete.

- Pre-run construction: v5 tests pass 9/9. The parent #5268 IR tests pass 5/5 when invoked from their own directory.
- Preserved setup errors: the first RED harness reached a missing-function `AttributeError`; the test was tightened to assert the absent API and then produced the intended RED failure. One parent-test invocation from the v5 directory failed during module discovery; the correct parent-directory invocation passed 5/5. Neither was a frozen runner invocation.

- Trigger: the v4 post-submit boundary probe found a decision disagreement for an infeasible deadline combined with unavailable resources.
- V5 preserves v4 byte-for-byte and isolates that precedence case under a fresh frozen corpus. Cost/budget values are synthetic same-unit values, not measured latency.
- Container gate: `STOP_NO_EXACT_RESOURCE_LEASE` per #5085. Docker/OrbStack invocation count is 0; no CLI inventory was attempted.
- #5273's full heterogeneous registry question remains broader than this successor.
