# Production release barrier probe A04

## Question

Does the late per-key resample treatment survive the current `ExecutorV13` terminal cleanup path when it uses the actual inherited `session_v5.Backend.release_all` method? The relevant boundary is whether deferred owner records are drained before the terminal event.

## Frozen inputs

- Main base: `3f24e85bff32a93fbc1ca244f7f249b843710743`.
- Candidate baseline: PR #7829 head `70c76483c46108bdd70bf2fb90679d948a5f156f`.
- The executor stack and inherited release method are copied from the frozen main base. The test extracts `Backend.release_all` from that exact `session_v5.py` source by AST and binds it as the base release method.
- The candidate treatment adds `_drain_owner_records()` in a `finally` block around its owner release call. The initial no-flush experiment failed because no release measurement was published before terminal. The candidate-with-flush then passed the same three cases.

## Schedule

A fake Xlib harness blocks the aggregate pointer query after a partial owner-release record. A production `ExecutorV13` run then reaches terminal cleanup while the query remains blocked. The schedule checks the exact PR #7829 candidate baseline, the late-resample treatment, and an injected failed retry sample. The terminal record must follow any emitted per-key receipt. The harness execution is synthetic and was run with host Python 3.14.5; no external services are used by the test. This is not a Doom or GUI run. The planned container run was stopped because OrbStack could not enumerate its image store; see `CONTAINER_STOP.txt`.

## Limits

This probe verifies a production-class executor and its current inherited terminal-release method under a controlled fake-Xlib schedule. It does not validate real X11 behavior, GUI integration, model-pending freshness, threat-exposed stale-policy handling, damage/ammo/progress response, MAP01 clear, or task effect. It does not satisfy Issue #59's live MAP01 exit gate.
