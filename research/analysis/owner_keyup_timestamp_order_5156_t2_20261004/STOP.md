# T2 STOP — auditor conflated finding with integrity failure

Allocation `OWNER-KEYUP-TIMESTAMP-ORDER-5156-T2-20261004-01`, frozen on main `96f7041fe6b3eb71127ac4eca0ed31d313c29ad2` and preregistered in Issue #5156 comment 5975301604.

- Candidate: exactly one invocation, exit 0. The raw record contains four `measurement_ready=true` values, including the two frozen malformed-order cases `ack_before_admission` and `release_return_before_start`.
- Auditor: exactly one invocation, exit 1. It rejected 4/4 predeclared audit mutations, but also put the expected scientific negative-control mismatches into its integrity-error list (`readiness_mismatch:*`) and emitted `STOP_AUDIT_INTEGRITY`.
- Retries: zero. No candidate or auditor was rerun.

Disposition: `STOP_AUDITOR_CLASSIFICATION_BUG`. Candidate raw and first auditor output are retained unchanged. Although the raw outcome is suggestive of `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED`, this T2 allocation does not claim a qualified scientific result because its frozen auditor cannot distinguish a faithfully observed hypothesis failure from corrupted evidence. A successor must use a new allocation/path and separate raw-integrity status from hypothesis disposition.
