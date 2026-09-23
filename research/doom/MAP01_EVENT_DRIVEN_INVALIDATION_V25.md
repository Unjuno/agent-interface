# MAP01 v25 event-driven invalidation

V24 proved the one-way cancellation contract live but evaluated only the latest
frame after each polling timeout.  It skipped the earliest already-changed
frame in two of four invalidations.  V25 moves the unchanged guard into the
observation dequeue path: every exact observation is evaluated in queue order
before the terminal predicate can advance the controller.

`event_driven_policy_monitor_v1.py` is the shared adapter.  It binds the source
to focus and pointer geometry, enforces a strictly advancing stream sequence,
loads the exact frame, and returns only an invalidation record.  Duplicate or
regressing sequence and image/binding/time failures become `UNKNOWN` and require
a new decision.  Like the underlying guard, the monitor cannot grant input,
classify the visual change, or prove success.

The retained v24 cover-4 replay feeds every ROI observation in capture order.
The event-driven monitor invalidates at sequence 200 with 921 changed pixels;
v24's timeout loop selected sequence 201, 138.003284 ms later, and evaluated it
208.776672 ms after that capture.  A second test verifies that a duplicate
stream sequence fails closed.  These tests establish dequeue semantics, not
live scheduling latency.

The controller also passes the monitor through its final cover-cancellation
wait.  Observations queued just before the model returns therefore cannot evade
the guard while the controller waits for terminal release.  The v24 controller
and frozen evidence remain unchanged.

A local diagnostic over all 382 non-retained full observation PNGs from the
v24 run measured full-image decode plus ROI comparison at 8.231 ms median,
9.918 ms p95, and 11.477 ms maximum on this host.  The measurement is not an
independently retained benchmark because those full PNGs are deliberately
excluded from the compact repository evidence.  It identifies a later
transport optimization: emit a bound lossless ROI or digest with the exact
observation so a guard need not reopen the full PNG.

V25 does not cancel the frontier model request.  Planner cancellation remains
a separate change because partial usage, session continuity, child-process
termination, and the absence of an executable answer must all be explicit.
No new live allocation is claimed here.
