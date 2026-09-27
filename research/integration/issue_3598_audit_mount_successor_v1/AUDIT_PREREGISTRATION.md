# Audit mount successor — Issue #3598

## H/T/D/C/U

- **H:** Mounting the complete immutable `prior_issue_3587/` directory at
  `/parent` will satisfy all filesystem dependencies of the frozen #3595
  raw-only auditor and allow independent reconstruction of the original three
  #3587 allocations.
- **T:** First perform one separate no-network/read-only-root mount/hash
  preflight. Verify the exact parent archive, source manifest, runner, v1
  auditor, #3595 v2 auditor, all three formal `allocation.json` hashes, and
  that `/out` is writable. The preflight must not import or execute
  `audit_v2.py` and must not modify evidence. Only if every preflight item
  passes, make exactly one fresh container invocation of the already-frozen
  #3595 auditor, mounting the whole parent directory at `/parent`, the 3 raw
  allocations read-only at `/evidence`, the v2 script read-only, and fresh
  audit output under `/out/audit-01`. No GUI/runtime/Xvfb/input. Any failure
  after the formal audit invocation starts is retained with no retry.
- **D:** `PASS_RAW_RECONSTRUCTION_ONLY` only if the auditor exits 0, writes a
  complete `AUDIT_V2.json` and raw SHA manifest, reconstructs exactly 3/3
  rows, rejects all 10 corruption controls on every row, and confirms source,
  image, request/report/image/effect/release/cleanup links. A preflight failure
  is `STOP_PREFLIGHT`; a formal invocation failure or any audit mismatch is
  `HOLD_OR_FAIL`. This cannot change #3587's official frozen-v1 HOLD or #3595's
  startup STOP.
- **C:** Exact same immutable allocations, archive, manifest, image and #3595
  auditor bytes. The only change is the full-parent mount layout and a new
  audit-only issue/output path.
- **U:** No fresh GUI task, no host/model visibility, model utility, latency,
  cost, human-tempo or broad-reliability claim. #3370 remains open.

## Frozen inputs

- Parent branch: `research/issue-3595-audit-3587-raw-v1`, commit
  `cd43deb8dba871c148d78b128d8d490df57585f4`.
- Exact v2 auditor SHA-256:
  `fd7ae177fd4b701ed45f4db35db8a0fedda41a2cbaaffa4ed3598dbb59be795a`.
- Parent archive SHA-256:
  `e2f50196e7ac67372fd0c480dbee473d26cc84d33e09806900f1efe7c8e7e624`.
- Linux/arm64 image ID:
  `sha256:63caf7c08199c6dc0712d000543aa19038a17ecbaf5ece309ec0c445a9c48a8a`.
- #3587 original frozen-v1 audit remains `HOLD_OR_FAIL`; #3595 v2 remains
  `STOP_BEFORE_RAW_RECONSTRUCTION`.

