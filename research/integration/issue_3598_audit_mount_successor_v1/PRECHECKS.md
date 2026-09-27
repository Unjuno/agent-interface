# Issue #3598 mount preflight

The hash-pinned preflight ran once in the pinned Linux/arm64 image with
`--network none`, a read-only root filesystem, and read-only parent/evidence/
script mounts. It did not import or execute the frozen `audit_v2.py`.

- Outcome: `PASS`, exit 0, 10 checks, no failures.
- Verified `/parent/freeze/`, `/parent/container_smoke.py`, `/parent/audit.py`,
  `/evidence/formal-01..03/allocation.json`, `/audit_v2.py`, and a writable
  `/out` mount.
- All parent archive/manifest/runner/v1-auditor/v2-auditor and three frozen
  allocation hashes matched the registered values. The archive embeds source
  `02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2`.
- Container Python: 3.12.3. Image identity was checked separately before the
  container start and matches `FREEZE_3598.json`.
- Exact raw preflight output: `evidence/preflight-output/preflight.json`,
  SHA-256 `2d8701cb83c6024ec9e188dadf36e293f9957f6fb4ed89370fe08f4c0ae0873e`.

This is only mount/hash readiness. The single formal audit-only invocation is
still pending; no GUI/runtime/input was created.
