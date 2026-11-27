# V39: cover release classification before planner acknowledgement

Base `236153b8ff381a64e49a5e588493a8cd8ce1f885` retained the #8956
counterexample: `cancel_invalidated_cover` sent urgent input cancel, then waited
on planner interrupt transport before reading an already available failed cover
terminal. The first strengthened healthy-terminal ordering assertion reproduces
that dependency without a new API or fixture argument. A separate initial four
method RED includes not-yet-implemented API errors; it alone is not the ordering
proof. All first/intermediate results are retained here.

## Adopted behavior

`PersistentPlannerAdapter.invalidate_turn(handle)` sets the matching answer's
local cancellation flag without remote transport. Remote interrupt-request
accounting is separate, so local invalidation does not consume a later matching
interrupt. Duplicate remote requests remain suppressed; an aborted transport
does not receive another request. Handles and session generation remain checked.

`await_turn` now retains the matching output schema while preparing a result,
then rechecks the handle/cancellation and publishes the immutable result under
the lock. It clears an invalidated answer and does not mark the turn terminal
until publication. New turns/session replacement cannot slip into a usage/parse
preparation interval. The review's usage-gated stale-answer counterexample first
fails on the earlier implementation and is retained separately. This does not
retroactively revoke a result already published before invalidation.

V39 invalidated-cover cancellation now performs local invalidation, cancel
write/flush, and strict known-empty terminal validation in that order. Only a
healthy terminal proceeds to synchronous remote planner interrupt. Failed/wait
boundaries save `cover-cancel-failure.json` exclusively before aborting the pending
planner transport; the primary exception retains a copied receipt. Save collision
or abort error adds a note without replacing the primary failure. All three
actual main callsites pass `args.out`. This lets a pending `await_turn` retire
before the enclosing pool joins it when the client close actually unblocks it.

Cancel-write failure still requires closure evidence; if closure is healthy the
remote interrupt is attempted and the write error remains a failure. Existing
strict terminal/release assertions remain. Local test stubs implement the explicit
invalidation operation; ordering assertions now require terminal verification
before remote ACK wait. The previous contradictory-bug characterization is
replaced with the repaired behavior; its original output remains in #8956's
unchanged evidence packet.

## Executed evidence

Eight new methods cover deferred remote request, duplicate/aborted request fencing,
stale handles, publication race, failed/wait boundaries, collision/abort faults and
selected Fake X composition. The latter uses actual capture/backend, Executor,
V4/V12 and planner adapter with a direct JSON-cloned message queue. While native
Fake X KeyRelease send remains held, keycode 38 is still down and the Executor
reports a failed/unverified terminal with its original release obligation. The
helper saves it, sends zero remote interrupts, and closes the substitute planner
transport before the test resumes its own native primitive. Its JSON row retains
held key, `native_resumed=false`, original terminal/obligation and local turn ID.
No physical release or actual process IPC is inferred.

The first composed fixture compared a JSON list to its pre-serialization tuple;
that failure is retained. The repaired assertion compares the same serialized
representation, without changing the terminal or obligation. First broad checks
on the earlier source had two saved-auditor setup errors because switching this
sparse checkout removed the retained historical `candidate.json`. Restoring that
exact Git blob materializes the fixture; no producer was executed. Unchanged
source line endings were also restored after an intermediate editing conversion.

Final clean tested source `a159d9e77c8d824a6e7865c6bd43d58fb1c34ea2`:
43 isolated modules / 316 methods, zero failures, one deliberate real-Codex skip
(315 executed), normal and optimized Python. Read-only correction review reruns
23 focused methods in both modes and finds no remaining actionable issue.
`normal/`, `optimized/`, and `intermediate-normal/` preserve source/status summaries
and every module log. Commands use `../check_map01_control_regressions.py
--output-dir <fresh path>`, adding `--optimized` for the second mode. Host: Windows,
Python 3.13.14, python-xlib 0.33, Pillow 12.2.0, MCP 1.30.0, openpyxl 3.1.5.
`MANIFEST.json` hashes this packet; original raw is not rewritten.

## Still unqualified

This repairs the invalidated-cover failure dependency, not all controller exits.
Healthy remote ACK wait, cancel write/flush, absent terminal waits, filesystem,
planner close, scheduler/GIL, native send/sync/readback and physical release are
not proven hard-time bounded. Natural failed cover-terminal handling elsewhere
still has its own synchronous interrupt path. Test-owned gate resumption/cleanup
is not task recovery, a new input authority or a replacement-session handoff.
Window incarnation, independent task effect, bounded task recovery and matched
efficiency remain open in #17/#59/#57. No display, model, game, WSL/container or
fresh live allocation was launched; optional remote CI is not claimed passed.
