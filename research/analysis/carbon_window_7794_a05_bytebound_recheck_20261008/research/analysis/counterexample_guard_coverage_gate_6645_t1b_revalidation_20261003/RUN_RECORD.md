# Invocation and custody record

| Activity | Host candidate calls | WSLc candidate calls | WSLc auditor calls | Outcome |
| --- | --- | --- | --- | --- |
| Earlier combined-harness construction | 3 | 0 | 0 | Development only; separate candidate raw not archived |
| WSLc environment preflights | 0 | 0 | 0 | Two container invocations, each exit 0; before HOLD recognition |
| Pure verifier_controls_01 | 0 | 0 | 0 | Exit 1; effectiveness assertion defect, retained |
| Pure verifier_controls_02 | 0 | 0 | 0 | Exit 0; six tests, 23 effective corruptions |
| payload_preparation_01 | 0 | 0 | 0 | Exit 0; three inputs/proposal, no launch |
| Frozen host_audit_01 | 0 | 0 | 0 | One host auditor, exit 0; 30/5/3, no errors |
| Final integration_verifier_01 | 0 | 0 | 0 | Exit 0; six pure tests, 23 effective corruptions |
| Local sparse integration_index_01 | 0 | 0 | 0 | Exit 0; absent-sibling stale-index diagnostic retained, not full-tree verification |
| Proposed WSLc neutral-ID formal | 0 | 0 | 0 | HOLD; no execution or retry |

The separate historical parent's formal candidate/auditor each ran once in OrbStack; those counts are not pooled with this package.

Captured commands use fresh output directories, no shell and no retries. Receipts hash source files and raw streams. They identify a host process, not a future container's state. Package SHA256SUMS covers retained files excluding itself and ignored caches. Old source/docs are inert .txt snapshots and remain unmodified.

This local checkout is task-owned; no other branch/path/worker resource is changed. The only shared tracked additions are the research ledger and directory index. Parent bytes are checked against the pinned manifest and freeze. No cleanup/deletion of evidence or branches is performed.
