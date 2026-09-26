# #4485 posthoc raw audit r8n2 — `STOP_POSTHOC_PROVENANCE`

## Disposition

Obstac construction passed, but the single frozen posthoc-audit invocation
stopped before the audit logic could read any input. The container mounted the
already-scoped study directory directly at `/study`; `audit.py` incorrectly
prepended the repository-relative source path and tried to open
`/study/research/integration/issue_3924_broker_exit_contract_v2/FREEZE.json`.
The actual file is `/study/FREEZE.json`.

This is an auditor path-configuration error, not a raw inconsistency or a
scientific result. The captured traceback and explicit disposition are in
`results/posthoc-audit-01/`. The audit report was not created. No broker, fake,
model, or network request occurred; the original raw tree was read-only and
unchanged.

The frozen one-invocation budget is consumed. Do not rerun or edit the r8n2
freeze, auditor, or output. The original Issue #4485 allocation remains
`STOP_AUDIT_IMPLEMENTATION_MISMATCH`; this attempted posthoc audit does not
alter it. Following `docs/ISSUE_FAILURE_CLASSIFICATION.md`, retain this
auditor limitation under #4485 and do not create another successor solely to
make an audit wrapper pass.

## Scope

No conclusion is made about whether the seven raw cases reconcile. This STOP
does not establish or refute the observed exit-zero discrepancy, and it cannot
promote a scientific PASS/FAIL under the original frozen D gate.
