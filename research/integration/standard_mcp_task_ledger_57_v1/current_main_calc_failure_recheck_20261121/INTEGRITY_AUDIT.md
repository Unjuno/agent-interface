# Custody and scope audit — 2026-11-22

## Snapshot provenance

This packet was copied byte-for-byte from the local `main` worktree at `897f4896d23dd127a4523dc4955e573dace7d674`. That source checkout was 67 commits behind the then-current main used for this audit (`174cfc36a019b6c71122d2c94109e25ae2ade2d1`). The packet is historical evidence for that source revision, not a current-main failure report. The raw files remain unchanged in this copy; source/copy comparison mismatches: 0.

## Legacy manifest findings

The original `SHA256SUMS` lists 400 entries. Rechecking those entries against the copied files found 1 hash mismatch and 54 files that were present but not listed; 0 listed paths were absent. The mismatch is `raw/commands.txt`: recorded `563b7a62f1700892c6dd89cb4c16a34de49601afa4efee26c90c8054f0c457b9`, current bytes `929cfcd6e5f5f79abafbb9d32f619a8f856607646470b2f3a4b1d9147d90a3e3`. Its content contains later command rows, but the exact mutation time and pre-mismatch bytes are unavailable. No attempt was made to reconstruct or replace the original.

`SHA256SUMS_RECHECKED` is a new snapshot manifest covering all 456 files in this packet other than itself: the 454 pre-existing files (including the legacy manifest) plus this audit report. This authenticates the copied snapshot from this audit onward; it does not retroactively repair the old manifest's provenance gap.

## Scope inconsistency

The original `RESULT.md` scope says no Docker operation occurred, while later findings in that same report and `conditions.json` describe isolated Docker runs. This is internally inconsistent. Treat the Docker observations as separately described historical runs only; the blanket scope sentence is not reliable for those later entries. The packet otherwise explicitly reports no live GUI task, external provider/model request, or formal allocation.

## Current disposition

The original diagnosis reported mixed, nonrepeatable Fake X composition outcomes and did not establish a runtime defect. It is superseded as a current blocker by merged PR #10366 (`338e2e8a`) and the clean-current-main focused recheck in [the receipt-order packet](../calc_save_controller_receipt_order_20261121/post-merge/win32-current-main-r02/RESULT.md). Retain this packet as a historical failed/held record; do not rerun it or promote its failures as current-main behavior without a new frozen reproduction.
