# Result — PASS_ARTIFACT_TRANSFER_PROVENANCE_RECONCILED

One preregistered offline CLI audit exited 0 under Python 3.12.10. It verified both Git blob identities and found:

- T8-retained captured stdout: 306 bytes, SHA-256 604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f, Git blob 39741cbea3f705d52611d82e4f431ec9e1d5b583.
- T7 PR-committed stdout: 308 bytes, SHA-256 4df6cbc2a680dc007a9bf837cfed8185cb6a197acc02e6d7505e355a0372b55d, Git blob 588d1816282ab17790faa3a94a939f9fce8d8bc3.
- The 306 captured bytes are an exact prefix; the only appended bytes are 0d 0a (CRLF), after the captured LF. Both files decode to equal JSON values.

Disposition is scoped to byte-level provenance of these two frozen Git blobs. The evidence does not identify which publication step normalized the line ending and does not prove any connector-wide transfer behavior.

T7 remains STOP_HOST_RECEIPT_SCHEMA_MISMATCH because its frozen host verifier rejected the auditor's actual field name. T8 remains PASS_RETAINED_RECEIPT_SCHEMA_AUDIT for its exact 306-byte captured-stream input; it did not audit the 308-byte T7 repository file. These earlier outcomes are unchanged.

No WSLc/Docker runtime, candidate, performance, memory, parity, hosted CI, or user-facing behavior was tested by T9.
