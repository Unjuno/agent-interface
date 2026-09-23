# Observable guard → CURRENTNESS_INVALIDATED adapter — first outcome

Decision: `PASS_OBSERVABLE_GUARD_CURRENTNESS_ADAPTER_SCOPED`.

One source-first formal invocation, seed `107120260918001`, reruns/replacements/tuning 0.

- primary adapter corpus: 180,000 rows; candidate/oracle mismatches 0;
- exact valid emissions: 64,701 = HARD_INVALIDATED 32,222 + UNKNOWN 32,479;
- valid SOFT_CHANGED/UNCHANGED critical emissions: 0 by construction/decision gate;
- rejected malformed/contradictory primary rows: 50,475; non-event rows: 64,824;
- mixed queue composition: 25,000 streams, CURRENTNESS_INVALIDATED input/delivered 50,005/50,005, loss 0, duplication 0, order errors 0, candidate/reference mismatch 0;
- old parent-domain reducer regression: 0 / 60,000 streams;
- authority promotions/grants, task-input, model and GUI actions: 0.

Independent audit passes with errors `[]`. Postformal frozen source rehash is exact for all seven source/plan files. Six copied-result corruption controls all reject.

Interpretation: exact observable-signal guard `HARD_INVALIDATED` / `UNKNOWN` one-way currentness outcomes can be normalized into the newly retained `CURRENTNESS_INVALIDATED` critical queue kind without laundering them into authority revocation, action rejection, focus, lease, safety or effect semantics. Caller/transport envelope identity remains external and is copied exactly rather than synthesized by the adapter.

Boundary: deterministic standard-library adapter/queue evidence only. This does not establish natural event frequency, live delivery latency, planner response, task correctness, or production ABI. A future live/retained-stream rung should test whether delivery causes the intended fresh-decision boundary while keeping authority independent.
