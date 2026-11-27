# Issue #57 late-usage port on current main — 2026-11-21

## What changed in this candidate

PR #10218 contributes late same-turn usage retention from timed-out App Server turns and a post-score adapter that joins hash-bound sidecars into the existing provider-attempt ledger. Its code was absent from current main. The candidate was reconstructed on main `381a21ace42891c2cd1e9cff3e231bec763ec2ba`, applying the original PR's unique code/test changes with a three-way patch. All 13 code, test, and README paths applied without conflicts. The 28 original evidence and attribute paths were transferred as well; one custody discrepancy was corrected additively and is described below.

## Current-main local verification

- 11-module discovery: **107/107 passed** normally in 81.641 s.
- Same discovery: **107/107 passed** under `-O` in 77.290 s.
- `py_compile` on all 12 changed Python files: passed.
- `git diff --cached --check`: passed.
- The first discovery attempt ran before the sparse checkout included `runtime/backends/x11_v1`; 90 tests ran and two test modules failed to import that missing local path. This run is retained separately and is not counted as candidate failure or success.
- The two transferred historical manifests cover 25 files and now verify with zero size/hash mismatches.

## Custody correction

The original PR #10218 head had `late_spool_usage_sidecar_20261104/commands.txt` at 738 bytes, SHA-256 `409af0a0e70852c2b2125c9e3f9b050980b870e2902738dc7406a1a4a809da55`; its manifest expected 739 bytes and SHA-256 `275ed1967585d05064c1cd7d6dc0c80706b518987d1a0b65155584105ad15750`. A one-byte CR insertion search found exactly one position matching the expected digest: offset 737, immediately before the final LF. That byte was restored in this candidate copy, and the historical manifest now verifies. The original PR/head was not altered. The additive [custody correction](../late_spool_usage_sidecar_20261104/CUSTODY_CORRECTION.md) preserves the discrepancy and recovery method.

## Limits and next gate

These are deterministic local App Server/spool/Fake X tests with synthetic provider streams. They do not establish real provider delivery/billing or prove that every runner calls `observe_late_usage`; the call remains explicit and post-score. They provide no GUI effect, MAP01 task success, matched efficiency, or recovery reliability result. Keep #57 open. The next runtime integration step is to wire this usage receipt path into a fresh prospective Issue #57 run without enabling dispatch until the trusted allocation and independent scorer gates are satisfied.

The initial sparse-checkout failure log, both successful raw logs, commands, exit codes and environment conditions are retained in this directory.
