# Fake X single-writer separation spike A01

Question approved by the user as “Fake Xだけで検証”: can one serialized input
owner service retained cancellation/expiry while an observation query is stuck,
without a second cleanup writer or accepting a late observation as fresh authority?

Baseline main: `30609dc1aa2a2a615e8ccb1ec77b317f0bd17a22`. This is a research-only
construction, not an adopted runtime, public cancel endpoint or live allocation.
The prior public-path A01 already demonstrates the blocking residual. Here both
arms use actual `X11Backend.key_state`, `pointer_button` and `release_all`, with
memory-only X transport/platform setup. The program loop, observation proof,
revocation state and scheduling are probe-owned. No actual bridge/dispatch,
visual grounding, PID namespace, physical X server or application is qualified.

Both arms hold CTRL + left button, obtain an observation, then attempt `a` +
right button and terminal cleanup. The sole intervention is moving the blocking
query from the input owner to an observation worker. Only the input owner calls
native input/release primitives. Cancellation publishes a retained Event; expiry
advances a fake monotonic clock to the original deadline. A wake is only a hint.
Revocation is sticky, advances an epoch and cleans up once. Late observation
replies cannot restore the old epoch. This schedule does not prove an atomic
check/use boundary against asynchronous server acceptance.

## Frozen finite matrix

1. coupled/healthy; 2. separated/healthy;
3. coupled/cancel; 4. separated/cancel;
5. coupled/expiry; 6. separated/expiry;
7. separated/duplicate_cancel;
8. separated/cleanup_sync_block;
9. separated/cleanup_emit_block;
10. separated/unknown_readback.

Cancellation, expiry and fault cases stop the observation query after the same
held prefix. Snapshot before resuming it. In 8/9 also block the actual backend's
cleanup sync/emission, snapshot there, then resume the backend before observation.
Case 10 raises during actual backend readback after fake releases. All blocking
Events have a five-second harness guard and are released in `finally`; that cap
is not a release guarantee or latency metric. Normal and optimized Python each
run the same finite construction once after source freeze. No formal/live ID is
consumed or replayed. First outputs refuse overwrite; retain failures separately.

## Decisions fixed before collection

- Healthy arms must emit the same ordered task press/release semantics and finish
  with verified fake-neutral state. Disabling all input is not success.
- In coupled cancel/expiry, the blocked query must leave CTRL/left held and no
  cleanup receipt before resumption; otherwise the control is not discriminating.
- Separated cancel/expiry/duplicate must revoke and return verified fake cleanup
  while query remains blocked; no later task press; one cleanup and one epoch
  change. Duplicate cancel must not cause a second release owner.
- Blocked cleanup sync: fake neutral may precede a verified receipt. Blocked
  cleanup emission: held state must remain. Neither counts as bounded release.
- Failed readback: fake neutral is insufficient for verification. Keep unknown;
  do not replay, re-ground, renew, reopen or infer application success.
- Every injected key/button event must come from exactly the owner thread.
- Audit reads only saved JSON, rederives the distinctions and refuses independent
  mutations: erased held state, fabricated verified receipt, late task press,
  second writer, duplicate cleanup and a resurrected observation epoch. Also
  reject a false boundary epoch, cleanup before revocation, false empty readback
  and reversed healthy release ordering. Publication and its event record share
  a memory lock; the lock is released before blocking backend cleanup.
  Empty read samples moved before releases must also be refused by replaying
  transport state at each sample position; readback comes from the owner thread.

Fake event clocks and externally advanced expiry are logical schedule markers.
The real backend receipt's monotonic timestamp remains in its own real-clock
domain and is not compared to fake timestamps. A functioning Python scheduler,
memory recorder and responsive input send/sync/readback are assumptions of the
positive separation cells. No OS timer, process isolation, GIL-stall tolerance,
trace-persistence isolation or atomic fence-to-server-acceptance is constructed.

Freeze probe/auditor/tests/plan and materialized runtime Python sources before
collection; bind raw to its freeze and preserve a postcheck. Save individual
events, request/epoch/deadline state, boundary snapshots, backend receipts,
unknowns, termination and conditions. No physical, task, recovery, efficiency or
real-time PASS may be inferred. A positive result only selects this separation
seam for actual caller integration; backend-stall handling remains a separate gate.
