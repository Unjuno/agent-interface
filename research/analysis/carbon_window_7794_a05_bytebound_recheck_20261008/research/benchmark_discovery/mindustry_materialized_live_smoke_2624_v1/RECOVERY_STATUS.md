# Recovery status — 2026-10-01

## Verified and preserved

- The two committed `source-freeze.part*` files concatenate to a 7,036-byte XZ archive with SHA-256 `0a53f87c2178068743c1f7f0ea06caab1550723d70a601c4d8fe3b99225eb2e1`, matching `SOURCE_PACKAGE.json`.
- The archive lists eight members: the frozen plan, construction record, `run.py`, `audit.py`, `test_audit.py`, environment, acquisition receipt, and freeze. The archive was listed only; no candidate, auditor, test, Java, or Mindustry process was run during this recovery.
- `FREEZE.json` pins the intended JAR/save/mod identities and records zero formal sessions before freeze, one planned session, and no post-freeze tuning/retry/replacement.

## Evidence boundary

This recovered V1 branch snapshot is pre-formal (0/1) and contains no measured result bundle. Issue #2624 later reports a V1 `FAIL_ORACLE_MISMATCH`, but that outcome is not independently revalidated by these source files. Do not turn the source-capsule verification into a scientific PASS or FAIL.

The active premounted-asset follow-up and later V2 allocation are separate work. Issue #2624 remains open; its newer runner/evidence requirements are not satisfied by this V1 source freeze. No experiment was rerun and no asset/JAR was downloaded or substituted here.
