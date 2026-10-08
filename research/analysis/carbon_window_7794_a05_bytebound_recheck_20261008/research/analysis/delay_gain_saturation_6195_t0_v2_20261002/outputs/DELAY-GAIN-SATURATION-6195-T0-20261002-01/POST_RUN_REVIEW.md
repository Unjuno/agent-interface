# Post-run review

## Preserved event sequence

1. Pre-formal construction tests: 2/2 passed; no formal output was written.
2. Frozen candidate: invoked once, exit 0, five rows retained in `candidate.json`.
3. Independent raw-only auditor: invoked once because candidate exited 0; exit 1 during its validation function. It raised `NameError` for undefined symbol `F` in the cap-check generator expression and did not create `audit.json`.
4. No retries or replacements. The allocation remains terminal `FAIL_AUDIT_EXECUTION`.

## Scope

The failure is an auditor implementation defect, not evidence for or against the hypothesis. Candidate rows are retained but have no independent validation. This does not establish physical control behavior or any runtime/product claim.

## Follow-up boundary

Do not edit this allocation's source or outputs, and do not rerun either formal command. Any future validation requires a separately preregistered successor with a new branch/path/allocation and its own start gates. The observed issue to address is the auditor's missing exact-fraction alias in the cap check.
