# T11 formal result — PASS

The single preregistered offline CLI invocation completed with exit code 0 and returned `PASS_T7_PUBLICATION_BYTES_CLASSIFIED`.

- Files checked: 11/11.
- Exact-source blobs: 0.
- Blobs equal to the frozen local/public source plus exactly one trailing CRLF (`0d0a`): 11.
- Frozen source-manifest claims checked: 6/6.
- Formal invocations: 1; retries: 0.
- Docker runs: 0; WSLc runs: 0.

All remote Git blob identities and byte lengths match the allowed source-plus-CRLF classification in the frozen T7 head. The local/public source bytes and SHA-256 values passed validation, and the six checksummed files in the source manifest matched those frozen source bytes.

This resolves T10's auditor implementation defect for a separate successor audit. It does not turn T10's first formal `KeyError` into a PASS: T10 remains STOP, and T7's original `STOP_HOST_RECEIPT_SCHEMA_MISMATCH` remains unchanged. The byte audit cannot determine which publication step appended CRLF, revise prior experiment outcomes, claim connector-wide behavior, or establish Docker/WSLc parity or performance/memory benefits.

The exact captured JSON output is in [audit.stdout.json](audit.stdout.json). The frozen command, hashes, controls, and scope are in [FREEZE.md](FREEZE.md).
