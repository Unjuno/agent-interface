# Issue #7409 T0 A01 — application-qualified draft fixture

**Disposition: `METHOD_PASS_SCOPED`.** The frozen OrbStack candidate and raw-only auditor each ran once (exit 0; retries 0). The auditor reconstructed all six rows and rejected all six output mutations.

This is an authored deterministic fixture only. It found the intended method distinction: disjoint edits merge after revision validation; same-field and read/write-dependency conflicts hold; an isolated UI context with a shared autosave backend and a task with an external effect are refused before draft creation. It does not test an actual application or establish the Issue's T1 human benefit.

- Freeze and protocol: [`frozen/`](frozen/)
- Formal raw outputs and run receipts: [`results/a01/`](results/a01/)
- Container mount preflight: [`results/preflight/`](results/preflight/)
- Full scoped result: [`REPORT.md`](REPORT.md)

Allocation: `APPLICATION-QUALIFIED-DRAFT-7409-T0-A01-20261005-01`  
Frozen base main: `19a6b723e58ccfd2b8265e88659589ef9223fcc9`  
Frozen source commit: `5a258dc1ef6ed72d8564e81579b88056702d5844`
