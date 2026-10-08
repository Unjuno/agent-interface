# Retained #1750 audit A3 — source-first workflow repair

Task `OPTIMISTIC-READWRITE-X11-RETAINED-AUDIT-A3-20260919-003` / Issue #1799.

## H
Unchanged scientific question from #1795: the immutable #1750 raw rows satisfy the original seven scientific gates and the parent failure is localized to its frozen v1 auditor's wrong gate cardinality (6 instead of7).

## T
Workflow is the only repaired factor. Publish exact PLAN/auditor/corruption source and SOURCE_FREEZE before any scientific audit call; remote readback; ownership reread; then exactly one A3 audit invocation against main-retained #1750 evidence hashes. Recompute all science from raw rows without parent candidate/formal imports. Corruption controls run only after the A3 result exists.

## D
PASS iff bound parent hashes match; rows12/3-family; exactly seven named gates independently true; candidate stale G0=0; surface-only G0=3; parent RESULT equals recomputation; parent disposition remains FAIL_INTEGRITY_AUDIT_GATE_COUNT; corruption controls reject; source/result integrity pass; audit invocation1/reruns0/live-reruns0.

## C
A PASS validates retained raw via successor audit only. #1750 remains FAIL_INTEGRITY and #1795 remains STOP_WORKFLOW_INTEGRITY.

## U
Audit-only. No live/model/runtime/latency/token/generalization claim.
