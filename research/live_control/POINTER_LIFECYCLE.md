# Pointer geometry and owner lifecycle — 2026-09-13

`input_owner_v5.py` is the next **unpromoted** pointer-owner candidate. It adds
observed geometry binding and bounded caller failure handling to v3. The shared
backend/program validator still uses its previous owner; OpenTTD has not been
operated through this candidate yet.

## What changed

- Pointer leases require `expected_surface` and `expected_geometry` as well as
  the observed focus. Geometry is `[root_x, root_y, client_width, client_height]`.
  Admission compares current geometry against that tuple and rejects a moved,
  resized, unmapped or destroyed target. Held buttons are also checked while
  the caller is idle. Surface/geometry loss invalidates the lease.
- `surface_context` is a read-only owner operation for retrieving geometry.
  Tests compare it with independently known test-window dimensions. The future
  snapshot backend must capture/bind this data with the image and context; a
  planner-supplied tuple must not establish its own authority.
- Owner-thread termination is observable. Waiting calls check for termination
  and fail instead of waiting indefinitely for a reply that cannot arrive.
  Unanswered calls have a two-second watchdog; a timeout cancels the supplied
  lease, requests owner termination and prevents further admissions/retries.
- Shutdown attempts cleanup of held input even after an unexpected thread
  exception. If cleanup cannot be verified, it records `cleanup_failed`, not a
  successful release. Startup/close waits are bounded; an unresponsive thread
  produces an explicit unverified-cleanup error. The owner is a daemon thread
  so it cannot by itself keep its parent process alive indefinitely.

These are caller/lifecycle bounds under a functioning Python scheduler, not
hard real-time guarantees. A watchdog returning an error does not prove that
the X server accepted a release. A stalled server may keep the owner blocked
in I/O until the server resumes or the surrounding session is terminated.
The session supervisor must handle that state; callers must not replace the
owner and resume input while the old connection's cleanup is unresolved.

## Real X11 evidence

`pointer-owner-04` completed **16 scripted checks in one owner session**. It
retains movement, held-button movement, wheel event delivery, keyboard keymap,
deadline/cancel/focus/overlay release and old-lease isolation checks. New checks
cover a moved window whose old point still lies inside it, resizing during a
hold, destruction during a hold, and querying a destroyed surface.

The release assertions now bind to the exact lease deadline; they cannot be
satisfied by a release event from an earlier case. Destruction may be detected
through focus loss or surface loss, so both are valid release reasons.

`pointer-lifecycle-01` injected two failures into **only the probe's private
Xvfb process**:

| Failure | Observed caller behavior | Cleanup evidence |
|---|---|---|
| Xvfb temporarily SIGSTOPed while button 1 held | pending move failed after 2.0002 s; subsequent retry rejected | after SIGCONT, button 1 was up, pointer stayed at the original position, queued moves were not replayed, owner thread stopped |
| Xvfb terminated while button 1 held | next move/retry rejected; no indefinite wait | owner recorded cleanup failure; release was **unverifiable** after server termination; owner and owned processes exited |

These are two single fault-injection cases, not a failure-rate estimate or a
general disconnection proof. The 2.0002 s value is watchdog behavior, not normal
input latency. It is not evidence of human-tempo operation.

## Failed cohort and correction

The first geometry/lifecycle candidate, `input_owner_v4.py`, caught
`BadWindow` for a destroyed surface but `GetGeometry` returned `BadDrawable`.
That stopped the owner unexpectedly. The new termination handling returned an
error to the caller and the thread-exit cleanup verified button release; the
probe nevertheless failed because an ordinary missing surface should have
been reported as a decision boundary rather than losing the owner.

`input_owner_v5.py` handles both errors for geometry and a disappearing child
during hit traversal. The v4 source, partial result and failure records remain
in `pointer-owner-03`. An earlier release-reason assertion there could match a
prior case; use the actual `thread_exit` record for the destroyed lease, not
that partial row's suggested `focus_changed` label. The corrected probe uses
lease-specific release matching.

## Still required before integration/promotion

1. Bind surface/geometry to the same snapshot sequence and lease as the image;
   reject inconsistent captures and retain final cleanup through executor errors.
2. Add complete-program pointer validation, bounded action durations and
   backend operations. Do not give planner code direct owner access.
3. Verify the combined backend on actual applications, including nested widgets,
   popups/grabs, input shapes, geometry changes and interrupted drags. Child
   traversal, geometry checks and XTEST enqueue are not one atomic transaction.
4. Use the saved OpenTTD fixture for actual assistant operation and record task
   success, failure and feedback timing. Preserve desktop/DOOM regressions.

This adds core semantics and fault handling; it is architecture churn, not
evidence for Research Freeze. No existing frozen source was overwritten.

From the repository root in Linux, using fresh output directories:

```sh
python3 research/live_control/pointer_owner_probe_v4.py --out /home/taka/pointer-geometry-fresh
python3 research/live_control/pointer_lifecycle_probe.py --out /home/taka/pointer-lifecycle-fresh
```

Each cohort contains source hashes and raw result/release records. The simple
X11 window probes do not count as agent application tasks or model evaluations.
