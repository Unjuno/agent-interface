# DECISION-POLICY-ACTION-GUARD-COST-R0B-20260918-001
H: acquiring/validating current evidence through a local AF_UNIX boundary remains cheap enough to preserve #1163's per-action deterministic guard without stale/ambiguous effects.
T: same record schema/validator/schedule; INPROC_CURRENT vs AF_UNIX_CURRENT; 60k matched reads/arm + 10k invalidation->refusal probes; source-first freeze; one formal invocation.
D: PASS only if correctness/integrity pass and socket p95<=1ms, p99<=2ms, median delta<=0.5ms, invalidation-refusal p95<=2ms/max<=10ms.
C: AF_UNIX is a controlled acquisition proxy; host scheduling affects tails.
U: container-local mechanics only; no live/X11/model/task claim.
Intent: preserve Astra-authored cached policy; remove repeated semantic re-decisions; fresh current evidence invalidates/yields; direct Astra remains baseline for novelty.
