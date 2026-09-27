# Issue #3598 result — raw reconstruction only

## Outcome

`PASS_RAW_RECONSTRUCTION_ONLY`, one audit-only invocation, exit code 0. The
hash-pinned v2 auditor reconstructed 3/3 immutable #3587 allocations with no
failed checks, rejected all 10 corruption classes in every allocation (30/30
rejections), and emitted a SHA-256 manifest for 66 raw files. No GUI, Xvfb,
runtime MCP server, or new input was launched.

## Preserved parent outcomes

- **Issue #3587 official frozen gate remains `HOLD_OR_FAIL`.** Its original v1
  auditor result is unchanged (122 checks, six false-failure assertions across
  three allocations: stale expected source revision, and a save-key logging
  expectation that the Tk binding prevents from reaching the logger). The
  later raw-only reconstruction cannot retroactively pass the preregistered
  #3587 gate.
- **Issue #3595 remains `STOP_BEFORE_RAW_RECONSTRUCTION`.** The frozen auditor
  was started once but the parent files it requires were not mounted; it
  stopped before loading allocation JSON. No retry was made under #3595.
- **Issue #3598 mount preflight passed** with 10/10 checks, including exact
  parent/archive/runner/auditor/allocation digests and writable output.

## Formal audit details

- Parent portable archive: `e2f50196e7ac67372fd0c480dbee473d26cc84d33e09806900f1efe7c8e7e624`.
- Parent source revision: `02b6efb970e66f2169c01c49b1fa6a4ebb5e23f2`.
- Container: OrbStack image `sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`, Linux/arm64, network disabled, root filesystem read-only.
- Independent auditor: exact #3595 v2 script, SHA-256
  `fd7ae177fd4b701ed45f4db35db8a0fedda41a2cbaaffa4ed3598dbb59be795a`.
- All raw evidence inputs were mounted read-only. The complete parent directory
  was mounted at `/parent`, satisfying the auditor's sibling-path checks.
- The raw SHA manifest and full JSON audit are in
  `evidence/formal-audit-output/audit-01/`. `AUDIT_V2.json` SHA-256:
  `fb97a0b4abcc8b177f85e5b7c75c90138e42c18f11ba2f571b34e2cfe006d26d`.
- Every original-size post-action PNG had already been visually checked against
  its exact independent fixture marker in the #3587 allocation; the v2 audit
  validates byte/hash links without changing those images.

## Scope boundary

This is evidence reconstruction, not a fresh runtime pass. It provides no
host-presentation acknowledgement, model-visible receipt or interpretation,
model task-use, useful-feedback latency, model usage/cost, human-tempo benefit,
or broad GUI reliability evidence. Issue #3370 remains open.
