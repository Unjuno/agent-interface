# T9 freeze — retained T7/T8 blob reconciliation

Recorded before the single formal validator invocation. This is an offline artifact-provenance audit, not a new WSLc allocation.

## H / T / D / C / U

- **H:** The T7 stdout file committed by PR #6983 is the T7 captured stdout retained as T8's exact input, followed only by CRLF (0d0a). Their decoded JSON values are equal; this does not identify why the committed file gained bytes.
- **T:** Compare only these immutable Git blobs:
  - T8-retained captured stdout: PR #6992 head a25ec6dd14a1686f44a4292a980c979867e4489c, research/analysis/wslc_receipt_audit_5309_t8_20261003/inputs/audit.stdout.json, blob 39741cbea3f705d52611d82e4f431ec9e1d5b583, 306 bytes, SHA-256 604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f.
  - T7 committed stdout: PR #6983 head 684831240f9848e850736781edb98322949e8d8a, research/analysis/wslc_retained_audit_5309_t7_20261003/audit.stdout.json, blob 588d1816282ab17790faa3a94a939f9fce8d8bc3, 308 bytes.
- Snapshot input file SHA-256 a904ef0bdd90fc12e2cb8d7f6a267c34a17e124e35bb3028c12e0d32eb754699 (1,846 bytes). Validator SHA-256 5a7735d0bdae368f39db8c6ea3531a5a4594031c7f7add8e15012f08c1e0f61b (4,358 bytes). Mutation-test SHA-256 245dba58e6e55415a8d6fb775502af394a870f3c516e2ebd6a97d7eacd5733ca (2,885 bytes).
- Runtime: Python 3.12.10. Formal command: python -B verify_artifact_transfer.py --input inputs/artifact_snapshots.json. Maximum formal CLI validations: 1; retries: 0. Candidate runs: 0; WSLc: 0; Docker: 0.
- The eight mutation tests were construction/rehearsal checks before this freeze. Their test setup also invoked the validator once on the exact fixture; that rehearsal is not counted as the formal frozen CLI validation and is not silently relabeled as preregistered evidence.
- **D:** PASS_ARTIFACT_TRANSFER_PROVENANCE_RECONCILED only if both snapshot Git blob identities and the captured SHA-256 match, byte lengths are exactly 306/308, the committed bytes equal the captured bytes plus exactly 0d0a, and both JSON values are equal. Otherwise STOP_ARTIFACT_PROVENANCE_MISMATCH.
- **C:** A mismatch supports incorrect snapshot/source attribution or a non-newline content change. A PASS is compatible with publication newline normalization; bytes alone cannot determine which tool or step appended them.
- **U:** This checks only these two retained blobs. It does not prove a connector-wide transfer defect, explain the normalization mechanism, measure runtime/performance/memory, establish Docker parity, or revise either earlier outcome. T7 remains STOP_HOST_RECEIPT_SCHEMA_MISMATCH; T8 remains PASS_RETAINED_RECEIPT_SCHEMA_AUDIT for its 306-byte input, not the 308-byte T7 committed file.

