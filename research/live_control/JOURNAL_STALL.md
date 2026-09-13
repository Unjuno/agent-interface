# Real X11 journal stalls: release passes, ordering regression retained

The persistent ReceiptJournal was placed in a session_v17 servo event callback
using the familiar Inkscape rectangle fixture. A wrapped binary file pauses either
write or flush at pointer_yield. Before pausing, the probe verifies an owned button
and X11 button mask 256. While the executor is still active and output remains
blocked, the probe checks both owned buttons and physical mask become empty.
After resume, it checks verified release and no pointer movement or continuation.

`journal-stall-01` failed before input: Inkscape window setup timed out. Its original
cleanup did not retain the application log. V2 preserves that log; the next run
completed all four cases. The original timeout's cause remains unknown.

| Case in journal-stall-02 | Terminal | Release while blocked | Receipt order |
|---|---|---|---|
| write / original 700 ms expiry | expired | verified | preserved |
| flush / original 700 ms expiry | expired | verified | preserved |
| write / explicit cancellation | cancelled | verified | FAILED |
| flush / explicit cancellation | cancelled | verified | preserved |

The write/cancel receipt for cancel_requested precedes the stalled pointer_yield
receipt, whereas source event order is the reverse. The probe let cancellation
and executor callbacks append concurrently to a single-writer journal. All records
are present, but source order is not preserved. The initial audit failed on this
ordering assertion; the final audit explicitly reproduces the retained failure,
checks record multiplicities and verifies all frame reconstructions/source hashes.
It does not waive ordering for a production gate.

This is a probe integration, not adoption into the interactive entrypoint. The
records are probe receipts, not actual model delivery receipts. Independent owner
release still works in these four known cases; task semantic success, permanent
I/O errors and public-runtime concurrency are not established here. No task speedup
is measured. Next serialize emission as the real entrypoint does, issue cancellation
from a separate caller, and ensure blocked logging cannot prevent cancellation's
authority flag from being set. Preserve this counterexample before promotion.
