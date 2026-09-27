# Audit/status addendum v2 — Issue #5062

The merged `out/audit.json` and original `audit.py` are preserved unchanged as the first formal audit output. Review against the H/T/D/C/U in Issue #5062 found that its conclusion label, `FAIL_PREREGISTERED_PREDICTION`, was not the preregistered D status. D explicitly requires `FAIL_CONTRACT_OR_AUDIT` for any mismatch.

`audit_v2.py` independently rereads the same immutable `out/raw.json` and rechecks the same timestamps, lower-offset translation, Lease decisions, host authority bound, 30s horizon, and shutdown/journal receipts. It performs no socket I/O and executes no cases. Its `out/audit-v2.json` records the required preregistered result `FAIL_CONTRACT_OR_AUDIT`, with one mismatch only: the 5.249s case was predicted to HOLD but submitted and was accepted because observed probe time left the wrapper's 5s reserve intact. No authority-extension or timestamp-integrity error was found.

This addendum supersedes only the status label, not the result or raw evidence. Raw SHA-256 remains the same across v1 and v2 audits. Neither the v1 files nor the completed experiment was edited or repeated.


