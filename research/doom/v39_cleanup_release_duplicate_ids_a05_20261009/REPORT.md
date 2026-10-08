# Issue #8681 cleanup identity reconstruction A05

## Result

`PASS_CONSTRUCTION_AUDIT` on current-main base `0455b0079ca29bcfe85153f280e592f5e96528f6`. One frozen synthetic candidate produced seven cases; one separate raw-only auditor passed 40/40 checks.

The four controls behaved as intended: a valid single identity and a valid distinct two-identity pair certify empty release; the legacy tokenless terminal remains accepted; a mismatched release token does not certify empty. The three ambiguity probes all report `input_terminals_complete=false`, `input_releases_verified_empty=false`, and `input_release_verified_empty=false`: duplicate accepted IDs with one terminal, and contradictory duplicate terminal rows in both orders.

The repaired source records duplicate accepted/terminal IDs in the receipt and prevents ambiguous event sets from satisfying terminal completeness. The focused regression suite passes 5/5, and the existing cleanup test discovery passes 20/20.

## Retained predecessors

A02 and A03 are preserved as construction STOPs before any case execution (wrong root path; then a freeze-field mismatch). A04's candidate and 30/30 auditor output are preserved, along with an explicit limitation: that auditor hardcoded expected outcomes by case name rather than recomputing control semantics from raw events. A05 supersedes those attempts for the independent construction audit; none is deleted or relabelled.

## Scope

This is synthetic event-reconstruction evidence only. It does not show duplicate IDs occur in production, run a controller or game, invoke a model or GUI, send OS input, or establish physical release or user-facing safety.
