# Critical-event capacity backpressure — formal result

Task `CRITICAL-EVENT-BACKPRESSURE-20260917-001`, Issue #668.

## Decision

**`PASS_CRITICAL_EVENT_BACKPRESSURE_SCOPED`**.

This is a deterministic container-only successor to #658. The predecessor invariant — one replaceable latest-state slot plus a separate ordered critical-event queue per session — is held fixed. The only primary factor is behavior when the fixed event capacity (3) is full: silent `drop_oldest` versus explicit `ack_backpressure`.

## Formal result

One post-freeze runner invocation produced 12 fixed rows (6 cases × 2 policies), with no retry or tuning.

- `fill_exact`: both policies retain event sequences `[1,2,3]`.
- `overflow_unacked`: `drop_oldest` silently evicts unresolved E1 and ends `[2,3,4]`; `ack_backpressure` returns explicit `EVENT_BACKPRESSURE`, performs zero state mutation, does not admit E4, and preserves `[1,2,3]` byte-for-byte.
- `ack_then_append`: after an explicit ACK through E1, the candidate reuses the freed capacity and retains `[2,3,4]` in order.
- `latest_state_during_backpressure`: while the candidate event queue remains full `[2,3,4]` and E5 is backpressured, ordinary state replacement continues to latest state sequence 6 without changing the critical-event queue.
- `cross_session_capacity`: session A stays full/backpressured at `[1,2,3]` while session B independently retains its own latest state and event `[2]`.
- invalid controls: future ACK, unknown-session ACK, repeated/non-monotonic ACK, and non-monotonic record sequence fail closed. Every non-mutating rejection preserves the complete state digest.

The candidate therefore prevents *silent local loss of already-admitted unacknowledged events* at the tested capacity. The overflowing event is not magically retained by this local buffer; explicit backpressure transfers responsibility to the upstream producer. This experiment does not solve that upstream durability/retry boundary.

## Integrity

Construction was excluded. Before freeze, 4/4 unit tests passed and 7/7 copied-evidence corruption controls were rejected. Two audit-only construction defects were repaired before freeze (null dropped-event handling; malformed-evidence auditor crash); no scientific mechanism/case/capacity/decision rule changed.

Formal audit passes with zero errors. Postformal source hashes match the freeze. Frozen tests re-pass. Eight direct mutations of the actual formal result are rejected, including candidate event loss, silent overflow admission, false mutation claims, erased ACK boundary, erased latest state, cross-session loss, laundering the negative control, and missing row.

## Boundary

Capacity 3 is diagnostic, not a sizing recommendation. This does not establish indefinitely absent-planner safety, upstream event persistence, ACK-loss recovery, distributed durability, event priority/coalescing, real watcher rates, planner attention, token savings, or latency. The next single-variable question is ACK loss/replay: if an ACK commits at the consumer but its acknowledgement is lost, can content/sequence-bound idempotent ACK handling recover without prematurely discarding unresolved events?
