# Existing runtime ready fence — retained result

Task: `LIVE-EXISTING-RUNTIME-READY-FENCE-20260917-002` (Issue #818).

## Disposition

**`FAIL_EXISTING_READY_LIVENESS`**.

A1 is retained separately as `STOPPED_OUTER_ORCHESTRATION_TIMEOUT` and is not pooled. A2 changed only orchestration granularity to one fresh case per outer container invocation; candidate/baseline source, exact runtime blobs, existing `ready` contract, 300 ms clock timeout and scientific gates stayed fixed.

## First outcomes

- exact v11 `endpoint_only`: later `clock` timed out **3/3**; endpoint announcement preceded runtime `ready` **3/3**.
- `existing_ready_gate`: later `clock` reached boundary **1/3** and timed out **2/3** under the same 300 ms budget.
- candidate ordering `ready emit <= ready append <= endpoint publication < initial observation <= clock emit` remained valid **3/3**; candidate false-publication/authority errors were 0.
- no task program events **0/6**; wrapper exit0 **6/6**; final owner release verified neutral **6/6**.
- exact `interactive_v27.py`, `event_socket_v11.py`, `session_v16.py` blob identities were preserved.

Candidate post-ready timing: endpoint publication -> initial observation median **308.979 ms**, range **263.676..343.077 ms**. Endpoint publication -> later clock emission median **309.718 ms**, range **264.425..344.268 ms**. The two timeouts correspond to **309.718 ms** and **344.268 ms** publication-to-clock emission; the sole boundary case was **264.425 ms**.

The frozen auditor reports `FAIL_AUDIT` only because its hard scientific gate expects candidate `clock` boundary in every case; its exact error list is the two candidate liveness misses above. All other frozen integrity checks pass.

## Interpretation

The existing `interactive_v27` `ready` record is a coherent **persistent-setup-complete** event, but it is emitted before the initial snapshot and before the stdin command loop. That remaining startup work is variable enough to consume an unchanged 300 ms command/event budget. Therefore it must not be promoted as a bounded command-readiness fence on this path.

This is not a speed result. It isolates the next integration question: whether an already-existing event after the initial snapshot (rather than a new readiness vocabulary) can be used as the publication boundary if #57 composition actually requires a bounded command-ready socket.

## Scope

One xterm/private-X11 retained offline artifact, host scheduling unpinned, no model/provider/task input, no cross-app or production ABI claim.
