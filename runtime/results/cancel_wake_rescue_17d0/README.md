# Retained cancellation-wake evidence: current adoption

Updated 2026-10-15 under the active user's FINAL v5. The original rescue README
is preserved byte-for-byte as README_HISTORY_20261008.md; its prospective
committee/quorum and pending-integration statements are historical, not current
operating requirements. FINAL v5 section 8.1 permits one worker to review,
validate and integrate; it adds no nonauthor review count or vote gate. Actual
repository permissions and protections still apply.
Frozen packet committee/descriptors are also historical provenance, not a new
operating rule for workers reading the retained experiment.

This adopts inert historical evidence from #7049 via #7296 and #8764.
The 214-file experiment packet is unchanged. All 213 manifest targets and the
original first-outcome raw SHA256 match. The original native auditor PID and
monotonic timestamps were not recorded; no values or approvals are invented.
The old local-ci.log is historical validation, not current hosted CI.

The current saved-only verifier runs the reviewed auditor's load/audit functions
with its guarded CLI suppressed. Normal and optimized Python each qualify all
18 saved rows, match their individual copies and reject four synthetic data
mutations. No collector, control/native module, original auditor CLI, pipe/FD
operation, thread, container, GUI or input runs. This checks saved consistency,
not independent authentication of the original execution or current resources.

The original comparison shows the distinction among blocking cancellation bytes,
discarded EAGAIN and a retained current-owner Event in an owned dummy-FD fixture.
It does not prove physical release, production safety, event contention/ABA,
multi-owner cancellation, hard deadlines, useful feedback, task effect or the
broader #17/#59 goals. New runtime work must qualify its actual authority and
backend path separately; this archive does not authorize a live experiment.

Windows initially converted the checkout's line endings, causing the first
saved-check attempt to fail at CONSTRUCTION.md. Git blobs were unchanged and
all differences were newline-only. Scoped attributes now preserve exact bytes;
CHECKOUT_RECONCILIATION_20261015.json records the repair. Original raw,
freeze and checksums were not rewritten.

Recheck into fresh output files from the repository root:

    python -B runtime/results/cancel_wake_rescue_17d0/verify_saved.py --output NORMAL_REPRO.json
    python -O -B runtime/results/cancel_wake_rescue_17d0/verify_saved.py --output OPTIMIZED_REPRO.json

Use the maintained safety-control agenda for the remaining independent-cleanup
and late-reply-fencing repair, not the historical committee procedure:
[Safety-control agenda](../../../docs/ideas/safety-control-agenda.md).
