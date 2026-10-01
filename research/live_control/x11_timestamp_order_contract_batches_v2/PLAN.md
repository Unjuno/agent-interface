# #2802 allocation 02 — same science, immutable batch execution

Allocation: `x11-timestamp-order-batched-20260922-02`.
Predecessor allocation `x11-timestamp-order-20260922-01` remains immutable STOP_CASE (3 complete, 1 partial, 20 unstarted).

## H
Unchanged scientific hypothesis from allocation01: for an ordered native event channel, same-timestamp co-occurrence, strictly increasing timestamp order, and observed channel order are distinct contracts. A local ordinal preserves A-before-B information that a set-valued same-timestamp fragment discards, while a strict-time-only rule can miss valid same-tick A-before-B.

## T
Scientific sources `actor.py`, `case.py`, `policies.py`, `upstream_monitor.py`, `audit.py`, and `test_policies.py` are byte-identical to allocation01. Same 24-case schedule, events, 80ms source bound, 10ms SPACED waits, 120ms H wait, two observers, packet retention, policy input and audit gates. Changed factor is execution serialization only: four immutable consecutive six-case batches. Per-case supervisor bound is 8s; each batch has a 38s internal envelope and is invoked exactly once. Batch N requires a unique absent receipt/case directory; no retry/replacement/pooling. After four COMPLETE receipts, `aggregate.py` creates one 24-case RUN.json consumed by the unchanged raw-only auditor.

Construction is excluded: one six-scenario block verifies that all case lifetimes fit the new bound and preserves timings. Formal is not allowed unless construction completes cleanly.

## D
Scientific PASS/HOLD/FAIL gates are unchanged from allocation01 and the exact reused `audit.py`: all 24 cases, source/process/packet/cleanup integrity, candidate/oracle prefix agreement, AB and BA burst ties, >0 co-timestamp false ordered-prefix satisfactions, >0 strict-time disagreements, and 12/12 corruption controls. Missing batch/case/receipt is STOP/HOLD, never partial PASS. Formal allocation count1, batch invocations4, reruns0, replacements0, tuning0.

## C
Batch boundaries add idle time and can change host scheduling/tie exposure. Tie frequency is not an endpoint; only the frozen existence discriminator is required. No natural race rate or latency comparison to allocation01 is allowed. Same timestamp still does not prove causality, and local event order is not global cross-client order.

## U
Same scoped limitations as allocation01: private Xvfb/core PropertyNotify only; no application semantic completion, dropped-event recovery, wrap/restart, multi-writer causality, model/task benefit, token/latency benefit, production or cross-platform claim. Execution timing is diagnostic only.
