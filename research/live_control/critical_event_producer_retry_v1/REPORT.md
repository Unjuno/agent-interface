# Bounded producer retention across critical-event backpressure and lost ACK

Task: `CRITICAL-EVENT-PRODUCER-RETRY-20260917-001`

Decision: **PASS_BOUNDED_PRODUCER_RETRY_SCOPED**

## Question

Hold the retained consumer semantics fixed at capacity 3 with explicit `EVENT_BACKPRESSURE` and one latest content-bound idempotent ACK receipt. Change only producer behavior after a rejected event admission: fire-and-forget versus one content-bound pending event per session.

## Container-first first outcome

- `py_compile`: PASS
- construction unit tests: **9/9 PASS**
- formal runner invocations: **1**
- formal reruns: **0**
- verifier: **PASS_VERIFY**
- post-result source hash recheck: **7/7 exact**

## Result

The fire-and-forget negative control submits E4 into a full `[E1,E2,E3]` consumer queue, receives `EVENT_BACKPRESSURE`, retains no pending event, and therefore still has only `[E2,E3]` after ACK-through-E1 later frees capacity. Opening capacity does not recreate E4.

The candidate retains exactly one pending E4 after the same backpressure. An exact retry while the queue is still full returns `EVENT_BACKPRESSURE` with unchanged consumer and pending state. ACK-through-E1 then commits while its response is withheld; exact ACK retry returns `ACK_ALREADY_APPLIED`. Retrying the retained E4 after that capacity change returns `EVENT_ACCEPTED`, produces `[E2,E3,E4]`, clears pending state, and E4 appears exactly once.

While E4 is pending, a distinct E5 returns `PRODUCER_PENDING_FULL` without reaching or mutating the consumer. Reusing E4 identity/sequence with changed payload returns `PENDING_EVENT_CONFLICT` with zero mutation. Session A pending/backpressure does not block session B. A duplicate E4 after successful admission is rejected `EVENT_NON_MONOTONIC` without extra admission.

All 10 frozen decision gates are true.

## Interpretation

Consumer-side fail-closed backpressure is insufficient by itself if the upstream producer treats the rejected event as fire-and-forget. One bounded producer pending slot closes that scoped loss path: it preserves the backpressured event until consumer capacity becomes available, while the already-retained content-bound ACK receipt removes lost-ACK ambiguity at the capacity-release step.

The producer pending slot is deliberately bounded to one event per session. A second distinct event is not buffered or silently substituted; it is explicitly refused upstream.

## Boundary

This is a deterministic single-process container fixture. It does not establish producer crash/restart durability, disk/fsync semantics, unbounded event-rate handling, multiple pending-event scheduling, priority/coalescing, distributed delivery, peer authentication, real watcher behavior, planner latency, token savings, or production queue sizing. The next question is producer restart durability of this one pending event only if a concrete integration path requires it.
