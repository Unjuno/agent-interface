# S27 current-main WSLc private-Xvfb boundary trial

A preregistered single 3,930 ms standard-caller trial between S23's scoped 3,920 ms pass and S25/S26's 3,940 ms safety-bound failures. The exact session/container names and conditions are retained in `INVOCATION-METADATA.json` and `CONDITIONS.json`; machine-specific paths are redacted. No global session or container inventory was run. The harness used a unique session, an exact generated-container-name preflight, network-none execution, read-only source/dependency mounts, full-CID retention, and exact cleanup.

Result: `PASS_SCOPED_3930MS`, 28/28 audit checks. Both task oracles passed, while runtime state for the old canceled call correctly remained UNKNOWN/replay-denied/`task_success=null`. See [RESULT.md](RESULT.md), [AUDIT.json](AUDIT.json), and [redaction hashes](REDACTIONS.json). Synthetic private Xvfb only.


The uniquely created WSLc session storage VHDX (227,540,992 bytes) is retained after session termination; its SHA-256 is in `POST_CLEANUP.json`.
