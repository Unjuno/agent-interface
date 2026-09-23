# Persistent runtime natural-ready gate v1

Task: `PERSISTENT-RUNTIME-NATURAL-READY-GATE-20260917-001`  
Issue: #815  
Publication base: `17d080a8f4e71af79b1d7ee51470f29d53fa7df9`

## H

The current persistent runtime already has a natural initialization milestone: `interactive_v27.py` emits `event="ready"` after `suite.prepare(...)` and `Backend(...)` construction and before its stdin command loop. If socket endpoint publication is gated by that existing event, a later bounded EventCursor wait should not spend its budget on startup.

## T

One primary variable only:

- `endpoint_only`: publish the observation endpoint immediately after spawning the child and starting the stdout consumer.
- `runtime_ready_gate`: publish only after EventCursor has appended an existing `ready` record with `authority="none"`.

After endpoint availability, both arms forward the same read-only `clock` command and wait for `clock` with the same 150 ms EventCursor timeout. Test child startup delay is frozen at 300 ms. Formal allocation is 3 cases/arm, counterordered, one outer invocation, no reruns.

The executable child is deliberately test-only. It preserves the existing event vocabulary (`bootstrap_note`, `ready`, `clock`) and startup/command-loop relation. Exact current-main `interactive_v27.py` is verified separately through GitHub source inspection. The local socket harness copies the relevant v11 EventCursor/CommandOnce bounded-forwarding structure but is **not byte-identical** to repository `event_socket_v11.py`; therefore this experiment is a scoped control-flow/liveness transfer, not an exact full-runtime replay.

## D

PASS only if baseline times out 3/3, candidate reaches the later `clock` boundary 3/3, candidate ordering is ready-before-publication-before-clock, all readiness/read authority remains none, three negative controls fail closed, source/audit integrity passes, and formal reruns are zero.

## C

A benefit could be specific to the authored startup delay and test child. The existing real `ready` event may still have different live GUI timing or may be too late/too broad for a production endpoint contract.

## U

Host scheduling is unpinned; n=3/arm is mechanism coverage, not a reliability rate. No model, GUI, token, task correctness, latency speedup, or product claim follows.
