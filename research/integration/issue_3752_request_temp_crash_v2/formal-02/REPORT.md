# Formal allocation 02 — scoped PASS

Allocation `issue3752-request-temp-crash-successor-02` ran exactly once in a fresh OrbStack Docker container. Runner disposition: `PASS_SCOPED_REQUEST_TEMP_UNKNOWN_NO_REPLAY`; errors: `[]`.

- Frozen base: `76965311d899815174b5ed081ff439bd4533ef63`.
- Source: `attempt.py` Git blob `70cc62b450c8b9c8aaa0db49b1e116388368fe4c`; CLI `__main__.py` blob `8a9178b7b8721b8a5471fabcfbeb1cb55976980c`.
- Runtime: Python 3.12 slim digest `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/arm64, OrbStack Docker 29.4.0, network disabled, read-only root/source, 512 MiB, one CPU, 32 PID cap, dropped capabilities, no-new-privileges, 64 MiB tmpfs.
- Child exited `29` immediately after writing/flushing a 134-byte strict prefix to `.request.json.tmp`. Its SHA-256 is `a68eae9cbd852ea5402d89c72eb4450e64021a2e300a7156480116de5a55b48c`.
- Two public `attempt-status` subprocesses each exited 2 and returned `unknown_or_incomplete`, `replay_allowed:false`, `process_state:"unknown"`, listing exactly `.request.json.tmp`. Both snapshots were identical.
- Public CLI `main()` reuse returned exit 2 / `REQUEST_PERSISTENCE_FAILED` / `operation_invoked:false`; the dispatch marker was absent and the complete run-directory snapshot remained identical. No request/report final record appeared.
- Raw JSON SHA-256: `6d0cc630d979b19263450f8220ac0bce184e0ebdc5ea267ab76f67d1e994ea68`.

This is runner evidence and awaits separate independent artifact audit. No broad durability, cleanup, native-effect, or full-adoption claim is made.
