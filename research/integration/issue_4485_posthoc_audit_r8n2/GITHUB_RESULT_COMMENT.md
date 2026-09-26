## Posthoc audit invocation 01 — `STOP_POSTHOC_PROVENANCE`

The one frozen r8n2 audit invocation exited 1 before auditing raw: `/study` was already the issue study directory, while the new auditor incorrectly prepended the repository-relative study path and looked for `/study/research/integration/issue_3924_broker_exit_contract_v2/FREEZE.json`. The actual mount root is `/study/FREEZE.json`.

The exact traceback and STOP record are retained under `research/integration/issue_4485_posthoc_audit_r8n2/results/posthoc-audit-01/`. No audit report was created; raw inputs were mounted read-only; broker/fake/model/network calls were zero. The frozen r8n2 one-invocation budget is consumed: no retry or code/freeze edit will be made under this allocation. The original #4485 `STOP_AUDIT_IMPLEMENTATION_MISMATCH` remains unchanged. This is an auditor-path STOP only and does not decide whether the seven original raw cases reconcile.
