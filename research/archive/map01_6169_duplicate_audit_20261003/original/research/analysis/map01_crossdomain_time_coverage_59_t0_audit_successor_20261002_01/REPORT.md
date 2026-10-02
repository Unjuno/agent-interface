# r133 / #6164 raw-audit successor

Allocation: `R133-6164-RAW-AUDIT-SUCCESSOR-20261002-01`  
Issue: #6169 · Parent evidence: Draft PR #6164

## Disposition

**`PASS_AUDIT_SUCCESSOR_SCOPED`**. One independent raw-only audit invocation passed after six in-memory construction/mutation controls. The candidate and predecessor auditor were not invoked. Retries: 0.

The parent audit's v38 fixture defect is confirmed: raw v38 contains one `post_control_score`, not zero. Candidate event-count maps for v38, v39 and OpenTTD match independently parsed raw. OpenTTD observer cardinalities are distinct and both correct: one transition-witness record (index 91) is passed to the candidate classifier; the full raw AIT stream contains 263 records and two unique states. The predecessor report's characterization of 1 versus 263 as an unexplained inconsistency was ambiguous; this successor resolves it from candidate source and raw.

## What remains unknown

No domain has identity-bound physical down/up intervals joined to independently timed useful effects under a compatible denominator. Therefore this is a method/audit result only. It is **not** a coverage-transfer PASS, physical occupancy result, useful-feedback result, task-success result, latency claim, or MAP01 exit. Issue #59 remains open; parent #6164 and its original `FAIL_AUDIT` remain unchanged.

## Reproduction boundary

The exact frozen raw files remain preserved in parent PR #6164 and were fetched from immutable source commit `279ee4aee96c5646360239409931821726566aa2`; all six Git blob IDs and SHA-256 values were checked before the single audit. This run used host CPython 3.11.9 and the standard library. It did not write raw files to disk, launch Docker/WSL, or touch GPU/model/game/GUI/input workloads. See `FREEZE.json`, `RUN.json`, `audit_result.json`, and `CONSTRUCTION_CONTROLS.json`.
