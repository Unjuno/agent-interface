# Diagnostic attempt record

- Formal auditor v1: one frozen invocation, exit 1 before row reconstruction because the dynamic loader omitted `__file__`; exact stderr is in `../FORMAL_AUDITOR_STDERR.txt`. No retry.
- Read-only audit v2: retained in `ATTEMPT_V2.json`; row reconstruction completed, but its utility aggregation used a different matrix-key shape and stopped with `KeyError`. Candidate and formal auditor were not invoked.
- Read-only audit v3: retained in `AUDIT_V3.json`; all 6,624 matrix rows were reconstructed with no row-related error. It found two control-output mismatches (revoked grant and protected constraint), so overall audit is `FAIL_AUDIT`. It reports 6,383 certificate-changing deviations and zero safe-beneficial reports in either frozen information partition. This does not repair the candidate outputs or change the formal HOLD.
