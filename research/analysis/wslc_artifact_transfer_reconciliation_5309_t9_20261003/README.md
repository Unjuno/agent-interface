# T9 — retained WSLc artifact-transfer reconciliation

Result: PASS_ARTIFACT_TRANSFER_PROVENANCE_RECONCILED.

This is a separate offline provenance audit. It did not rerun T7/T8, launch WSLc or Docker, or revise either historical disposition.

- captured_stdout is the 306-byte T7 stdout copy retained and schema-audited by T8 (Issue #6990 / PR #6992).
- t7_committed_stdout is the 308-byte file committed in PR #6983.
- Exact source Git commits and Git blob IDs are frozen in inputs/artifact_snapshots.json.
- The validator checked byte counts, Git blob identities, the captured SHA-256, exact CRLF-only suffix delta, and equal JSON values.

The two immutable repository snapshots differ by a trailing CRLF after the captured LF. This does not establish why the bytes changed during publication. T7 remains STOP_HOST_RECEIPT_SCHEMA_MISMATCH; T8 remains PASS_RETAINED_RECEIPT_SCHEMA_AUDIT for its 306-byte input. No Docker parity, WSLc benefit, memory, performance, or runtime behavior is measured.
