# Archival qualification — host-only construction

This directory preserves a finite host construction package. Its 11 tests
exercise separate candidate/auditor subprocesses and fail-closed handling for
malformed synthetic soft-event inputs; they do not constitute the separately
allocated WSLc construction or a live #59 threat-control result. The later
WSLc T0b allocation is preserved separately on main by PR #6609. Do not pool
the two allocations or infer production/game/model/GUI effects.

The original `SHA256SUMS` is retained unchanged. Its final line names
`REPORT_research_soft_event_context_6561.md`, while the branch contains
`REPORT.md`. The report bytes hash to the exact digest on that line; mapping
only that filename to `REPORT.md` verifies all five manifest entries. This is
a stale filename in the manifest, not a content-hash mismatch. No original
file or checksum was rewritten.
