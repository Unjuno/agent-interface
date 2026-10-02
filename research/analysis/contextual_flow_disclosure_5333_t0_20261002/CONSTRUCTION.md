# Excluded construction history

These are preparation checks, not formal candidate/auditor invocations.

1. Initial WSLc contract check: 6/6 tests passed. It preceded generic protected-sink handling and matched-pair invariance checks.
2. Follow-up WSLc contract check: failed 1 test (`test_all_frozen_rows_reconcile`); the new independent matched-pair gate also compared each pair's case identifier, so it rejected its own declared fixture pairing. Other five tests passed. No formal candidate or auditor ran.
3. Correction: compare all pair fields except the explicit varying context axis and the case identifier used only to name the paired rows. This construction failure is retained; it is not counted as a formal result and does not alter any prior Issue result.
4. Final WSLc construction check after the correction and generic protected-sink/policy matching: 6/6 passed. A separate WSLc output-mount smoke wrote a host-visible file successfully. Every container was CPU-only, network-disabled, `--pull never`, and removed on exit; no formal candidate/auditor was invoked.
5. After adding the preregistered stale-release row, the final nine-card construction suite again passed 6/6 in WSLc; the output mount remained available. Formal candidate/auditor counts are still zero.
