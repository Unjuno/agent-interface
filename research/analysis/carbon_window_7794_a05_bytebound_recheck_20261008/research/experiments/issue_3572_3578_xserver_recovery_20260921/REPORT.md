# X-server lifetime branch recovery: #3572, #3578, and #3579

This report rescues three unmerged remote branches as an additive evidence
record. The predecessor allocation artifacts remain byte-for-byte unchanged.

## H/T/D/C/U

- **H — Hypothesis:** A per-X-server lifetime token can distinguish a stale
  receipt from a new X server even when XID and typed identity fields are
  reused. The recovered evidence does not establish this hypothesis because
  the formal raw is blocked by provenance integrity.
- **T — Test:** #3572 froze one 16-row formal allocation and invoked it once;
  it stopped during result serialization because `/freeze.json` was not
  mounted, leaving no raw result. Its frozen rule forbids editing or rerunning
  that allocation. #3578 is the distinct one-invocation successor: 4 pairs,
  16 rows, and 28 negative controls, with zero retries. #3579 is an audit-only
  successor over the retained #3578 raw; this recovery independently replayed
  only that audit in the same pinned `linux/arm64` image
  `sha256:fa36aca92a682831d72b7e49bf05a9c6e31e68eadb06f3d2728360ceb1e9f6cb`,
  with networking disabled, candidate and input mounts read-only, and fresh
  temporary audit output. No Xvfb instance or task input was started.
- **D — Data:** The #3572 STOP is preserved at
  [`issue_3572_xserver_lifetime_formal_01/STOP.json`](../issue_3572_xserver_lifetime_formal_01/STOP.json):
  one invocation, exit 1, `FileNotFoundError: /freeze.json`, no raw, and no
  scientific PASS/FAIL inference. The #3578 raw remains SHA-256
  `9ae2ae5535783dfcd0258da0fd6ac2d42c7bf38962f4e65edeb5d0a33c6755e5`;
  its recorded candidate decision is scoped PASS, but the audit is STOP/HOLD.
  The frozen file binds source-manifest SHA-256
  `19d8deabf2054ede185bafdd4e1afc96f12b907c5c00b05397f4e2a6c1bfb660`,
  while the manifest actually bound into the raw is
  `f04218a37ceef81df305a7242adb8c0fae75fae5dce555901d45577e73b5db3b`.
  The original #3579 audit-v2 output and this read-only reproduction agree
  byte-for-byte: `STOP_OR_HOLD_AUDIT_V2`, error
  `freeze/source manifest SHA-256 mismatch`, 16 rows, 4 pairs, 28 controls;
  result self-hash and listed source-file hashes verify, and all 9 corruption
  challenges are detected. The unit tests against each frozen #3572 and #3578
  source directory passed 8/8 in the pinned image; these are construction/unit
  checks only and do not override either formal STOP.
- **C — Controls:** The original allocation freezes, source manifests, raw,
  STOP/audit JSON, and runner sources are retained at their original paths.
  Formal allocation #3572 and #3578 were not rerun or edited. The independent
  audit reproduction wrote only to a fresh temporary output directory; it did
  not alter the retained raw or prior audit result.
- **U — Unknowns:** No verified formal conclusion can be promoted from the
  #3578 candidate decision while the freeze/manifest binding is inconsistent.
  The experiment is limited to a deterministic Xvfb/Xlib fixture and says
  nothing about production X11, GUI action authority, or general reliability.
  Any further formal test requires a separately frozen successor with the
  final manifest hash bound before its one allowed invocation; do not repair or
  replay these historical allocations.

## Reproduction record

The audit-only reproduction used the frozen auditor without source edits and
exited 1 on the same provenance mismatch as the retained #3579 result. The
reproduced JSON was byte-identical to
[`issue_3579_xserver_lifetime_audit_01/audit_v2.json`](../issue_3579_xserver_lifetime_audit_01/audit_v2.json)
(SHA-256 `cfa4ad73439161172fee814693ecc74321b21863f2a340ac1f9f94fc0d0520f9`).
This is a diagnostic confirmation of the recorded STOP, not a new formal
allocation, a correction of the historical freeze, or a scientific PASS.

## Navigation maintenance

The current main workspace-index gate also exposed four pre-existing direct
`research/` directories missing from `ROOT_NAMESPACE_MAP.md`; links for those
existing directories are included so the rescue PR can pass the current
navigation gate. This is navigation-only and does not reclassify their
scientific status.
