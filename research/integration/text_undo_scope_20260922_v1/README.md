# Retained 24-case Undo-scope evidence: delivery continuation

Issue #4043 records delivery of the already executed `text-undo-scope-20260922-01` allocation. This is not a new GUI/formal run and is not retrospective GitHub preregistration. Preserve closed #2076/#3936 and the original local failures, freezes and result unchanged.

The exact 202 old source/raw/metadata files are retained inside the sibling [history evidence capsule](../text_undo_history_guard_v1/README.md), under `previous/` after its stdlib-only unpack step. All 202 were compared byte-for-byte; all three original raw audit outputs were independently rerun without GUI and match their original hashes.

Original outcomes: PASS_UNDO_SCOPE_BOUNDARY_SCOPED, with 9 COMPENSATED_SCOPED, 3 FAIL_COMPENSATION_COLLATERAL and 12 ABORTED_PARTIAL_NO_UNDO across 24 fresh processes. All endpoints were neutral. The 3 collateral failures and 12 unresolved/no-Undo rows are not compensation successes. Old startup/focus construction STOPs remain retained.

The original historical publication notes correctly reported an unavailable write path in that conversation. They remain unchanged inside the capsule. This dated continuation uses the now available GitHub writes and a reviewable PR; actual merge/readback status is in #4043. The new 12-case edit-history allocation is distinct and is not pooled with these 24 rows.
