# Issue #4649 — formal allocation 01

## Decision

Overall: **FAIL_AUDITOR_ROBUSTNESS**. The single formal Docker runner returned `PASS_FULLPATH_BYTE_AUDIT_LOCAL_AMD64_SCOPED`, but the preregistered gate required all eight corruption controls to reject. Only six rejected: `drop_input_row` and `input_digest` were accepted by independent auditor v1 as PASS with no errors. Do not promote the runner PASS into an overall PASS. The formal runner was not repeated.

## Evidence

- Intake main: `522ff97664c12399e94e28462688afc905732373`; frozen source commit: `ea66b59cfa45674d24e74de5ea0383f1ee1d3eb2`.
- Manifest SHA-256: `8180a34bb58ca94ac2734baba0cc84e6316144f37ffac7bb5977d2d6927e7438`; freeze SHA-256: `4665fbf32c86d66dcea3c6efdd6b073c39486321fae48ec8f07104de325b2a9f`.
- Local image ID: `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, CPython 3.12.14. Docker 29.8.0.
- Formal `FORMAL.json` SHA-256: `aa7de87e5cf0644eb5bbe645d34d9273a8fbefccf041faea12b4e6933886f6b7`; independent audit `AUDIT.json`: `a76f9007791d09c49f38b8d10a3e3011883ffee71015d25c1ae13edd30ad09e5`; controls `CORRUPTIONS.json`: `c1c572593d5e6e784ab168bdf4656742ac62e0bbafc22cbcb2b6c8739132a59c`.
- Local evidence ZIP SHA-256: `11be990ab08957b6c60b0fc6b3728a5e16b44089f423196efe89ee7c823dd05c` (7,915 bytes; 12 members, each verified against extracted originals). The ZIP is retained in the local research workspace; this GitHub record does not contain the ZIP bytes.
- Docker used `--pull=never --network none --cpus=1 --memory=1g --pids-limit=64 --read-only`; only tmpfs and dedicated output mount were writable. No Actions/workflow or remote runner was used.
- Preflight 01 STOP and corrected preflight 02 PASS are preserved locally. Exactly one formal runner invocation; auditor robustness controls are separate.

## Interpretation and preservation

The auditor recomputes the frozen input table but fails to compare the result JSON's own `input_sha256` ledger to that table. This explains the two accepted ledger mutations and is an auditor validation gap, not evidence of changed inputs. The six other controls returned structured FAIL. Historical raw/formal evidence is ARM64; this local run is amd64 and makes no ARM64-equivalence claim.

Keep the frozen v1 auditor, runner output, and this failed allocation unchanged. Any repair/re-audit must be a separately identified successor with its own H/T/D/C/U, additive path, and local Docker allocation. No CI was run.
