# A03 execution record — STOP

## Formal outcome

**STOP before analysis; no scientific result.** The frozen analyzer was invoked once with its preregistered command. It exited 1 because the output parent `results/` does not exist (`FileNotFoundError`). The frozen allocation permits zero retries, so the directory was not created and the analyzer was not rerun. The independent auditor was not invoked because there was no analyzer output to audit.

See `RUN_RECORD.json` for the exact command, stderr, counts, immutable input digest, and disposition.

## Interpretation boundary

This is a procedure/setup failure, not evidence for or against the hypothesis. No cell estimates, paired contrasts, or interaction estimates were produced. A01 remains `HOLD_AUDITOR_GATE_FAILURE`; A02 remains `PASS_AUDIT_ONLY`. Neither predecessor artifact nor disposition was changed. Any further analysis requires a separately preregistered successor allocation with a corrected output-path contract; this record is not permission to retry A03.
