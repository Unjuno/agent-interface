# #1748 Deterministic replay boundary sufficiency

## H
For a deterministic runtime, the same initial-state identity plus every external state-affecting boundary event, typed payload, and total order is sufficient for exact replay and one-step fork replay. Dropping order, MODEL payload, AUTH events, CLOCK/TICK events, or TOOL payload is not sufficient in general.

## T
Finite runtime with observation/model/tool bits, authority generation, logical time/deadline, typed REQUEST outcomes and admitted effects. Exhaust every event sequence of length 0..5. Record format is initial_id + strictly monotone sequence numbers + typed event/payload. Compare candidate replay to an independently structured imperative oracle. Exhaust fork(prefix)+one alternate event for all sequences length <=4. Build incomplete-record signatures and require outcome ambiguity for five omitted information classes. Independent auditor recomputes the full space.

## D
PASS_DETERMINISTIC_REPLAY_BOUNDARY_SUFFICIENCY_SCOPED iff exact replay mismatch0, fork mismatch0, sequence-integrity errors0, all five incomplete views have >0 ambiguous signatures with distinct outcomes, four corruption controls reject, independent audit/source integrity pass, formal1/reruns0.

## C
Real systems may have unrecorded nondeterminism. Total order is sufficient here but stronger than necessary for commuting events.

## U
Analytical deterministic boundary theorem only; no production replay/storage/GUI/model/latency claim.
