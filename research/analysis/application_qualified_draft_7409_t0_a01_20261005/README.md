# Issue #7409 T0 A01 — application-qualified draft fixture

**Original process output:** candidate and raw-only auditor each ran once (exit 0; retries 0); the original `audit.json` reports `METHOD_PASS_SCOPED`, with 6/6 reconstructed rows and 6/6 output mutations rejected. **Post-run qualification:** `HOLD_AUDIT_WEAKNESS`; the revision-check gate was self-asserted rather than evidenced by a base/current comparison.

This is an authored deterministic fixture only. Its raw outputs show disjoint edits merged, same-field and read/write-dependency conflicts held, and shared-backend/external-effect cases refused before draft creation. The original files remain unchanged; see the post-run qualification before treating the result as accepted. No actual application or Issue T1 human benefit was tested.

- Freeze and protocol: [`frozen/`](frozen/)
- Formal raw outputs and run receipts: [`results/a01/`](results/a01/)
- Container mount preflight: [`results/preflight/`](results/preflight/)
- Full scoped result: [`REPORT.md`](REPORT.md)
- Post-run gate qualification: [`results/post_run_review/REVIEW_QUALIFICATION.md`](results/post_run_review/REVIEW_QUALIFICATION.md)

Allocation: `APPLICATION-QUALIFIED-DRAFT-7409-T0-A01-20261005-01`  
Frozen base main: `19a6b723e58ccfd2b8265e88659589ef9223fcc9`  
Frozen source commit: `5a258dc1ef6ed72d8564e81579b88056702d5844`
