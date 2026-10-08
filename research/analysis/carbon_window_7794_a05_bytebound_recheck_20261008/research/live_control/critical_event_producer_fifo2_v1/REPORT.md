# Durable ordered two-event producer pending queue — retained result

Task `CRITICAL-EVENT-PRODUCER-FIFO2-20260917-001`, Issue #717.

## Decision

**`PASS_DURABLE_FIFO2_PENDING_SCOPED`.**

Six first outcomes, three per policy. Formal measured IDs were never rerun or replaced.

- `single_pending`: after E4 is durably pending, E5 is explicitly `PRODUCER_PENDING_FULL`; SIGKILL/restart recovers E4 only. ACK-through-E2 plus exact lost-response replay returns `ACK_APPLIED` then `ACK_ALREADY_APPLIED`; E4 admits once; final consumer `[E3,E4]`; final pending empty; fresh restart does not resurrect E4.
- `fifo2_pending`: E4/E5 are durably retained in exact FIFO order across SIGKILL/restart. E6 is `PRODUCER_PENDING_FULL`; attempting E5 before E4 is `PENDING_HEAD_REQUIRED` with zero mutation. After ACK-through-E2, E4 then E5 admit exactly once; final consumer `[E3,E4,E5]`; final pending empty; fresh restart reproduces the same state.

Frozen read-only audit: counts `{single:3,fifo2:3}`, errors `[]`. Three aggregate corruptions plus one source-hash corruption are rejected 4/4.

## Supervision incident

The one formal shell invocation exceeded the outer 45-second tool supervision window after all six `result.json` rows and `aggregate.json` had already been written. The initially opened `audit.json` is zero bytes. No formal ID was rerun. The unchanged frozen auditor was then run read-only over the retained complete aggregate and returned PASS. This is a supervision/output incident, not a scientific rerun.

## Boundary

This establishes only a trusted-local bounded depth-2 durable FIFO pending mechanism. It does not establish unbounded producer rates, capacity sizing, priority/coalescing, multiple producers, power-loss/storage-controller durability, distributed delivery, peer authentication, planner latency or throughput.
