# Freshness backpressure formal v2
TASK: FRESHNESS-BACKPRESSURE-CRITICAL-RETENTION-FORMAL-20260917-002
BASE: a1f17a1b1b018da83a10d3e2f2d114127424f93c
H: exact merged #1008 reducer preserves every critical edge exactly once/source-order while coalescing only fresh noncritical state within scope.
T: exact contract blob404a452a..., independent oracle, fresh seed100820260917002, 25000 random batches plus exhaustive streams length1..3, fixed malformed/boundary controls, one formal invocation.
D: PASS iff all candidate/oracle outputs match, critical loss/dup/reorder0, stale-current0, cross-scope merge0, controls pass, authority0, audit/corruption pass, reruns0.
C: critical-kind allowlist quality and pathological critical storms remain outside this queue-semantic formal.
U: synthetic queue semantics only; no model/task efficacy claim.
