# Parallel worker branch recovery — Issue #4439 v1

## Provenance and scope

- Source remote branch: `research/x11-region-frame-move-4439-20260927`.
- Exact source tip: `7cbd494b42763048c6ac0b48a2400c7ef3107fcd` (2026-09-27 23:42:57 +0900).
- The 21 files under `original/` are copied byte-for-byte from that tip's `research/observation_gating/x11_region_frame_move_q5t2_v1/` subtree. The original paths are retained inside this recovery directory; the source branch's full commit history must remain reachable by an archive tag before any remote-ref cleanup.
- This is a distinct parallel-worker branch from the original branch recovered by PR #6070. It is not the v2 result merged by PR #4903.

## What the preserved records say

- Construction records are mixed and remain separate: attempt 01 `STOP_XAUTHORITY_NOT_INHERITED`; 02/03 `HOLD`; 04 `PASS_CONSTRUCTION_DISCRIMINATOR`. The self-test records separately preserve setup STOP, a control-polarity HOLD, and a synthetic-only PASS.
- `FORMAL_01_STOP.json` records one formal invocation that stopped before case 0 because the output directory already existed: 0 formal rows, no raw formal file, and 0 X11 sessions. The recorded runner and auditor SHA-256 values match `original/runner.py` and `original/audit.py`.
- The failed synthetic self-test JSONL remains malformed as retained in the source branch. It is part of a recorded setup failure and has not been repaired.

## Integrity hold; no result promotion

The current #4439 Issue chronology and this branch's STOP record conflict with the canonical v1 `REPORT.md`/`RESULT.json` on main, which claim 27/27 formal cases passed under the same allocation. The Issue and main's existing `RECOVERY_STATUS.md` correctly retain `HOLD_CONFLICTING_RECORDS_AND_INCOMPLETE_RAW`; this archive does not resolve that conflict or validate either claim. The required full raw archive remains incomplete. Do not pool, replace, or reinterpret these records, and do not rerun the consumed allocation or reconstruct missing raw parts.

During this recovery, only original Git blobs, JSON/JSONL syntax, and the declared runner/auditor source hashes were inspected. The runner, auditor, X11 fixture, formal session, and scientific audit were not executed. This addition preserves provenance for later review; it is not a scientific result or authorization to run a successor.
