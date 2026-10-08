# Freshness-aware critical-event retention formal v2 — first outcome

Decision: **`PASS_FRESHNESS_BACKPRESSURE_FORMAL_SCOPED`**.

Exact merged #1008 contract Git blob `404a452aa304b4bde73ec0182450d241e2a744af` was held byte-for-byte. Formal seed `100820260917002`; exactly 25,000 fresh random batches containing 397,966 records, plus 4,368 exhaustive valid short streams.

Results:
- random candidate vs independently structured oracle: **25,000/25,000 exact**;
- exhaustive candidate vs oracle: **4,368/4,368 exact**;
- critical input records observed: **245,704**;
- critical lost/duplicated/reordered batch errors: **0**;
- stale noncritical delivered as current: **0** batches;
- delivered noncritical scope-cardinality violations: **0**;
- output authority errors: **0**;
- fixed malformed/boundary controls: **10/10 PASS**.

The result formalizes the scoped queue contract: valid critical edges survive exactly once and in source order regardless of age, while noncritical state is freshness-filtered and coalesced only to the newest fresh row per `{session,target,stream}`. Stale state is counted rather than relabeled current, and scope boundaries are preserved.

Formal invocation: 1; reruns/replacements/tuning: 0. Independent audit passed all 14 checks with errors `[]`; five copied-result corruption mutations were all rejected.

Interpretation boundary: this validates queue semantics only. The authored critical-kind allowlist may be incomplete, retaining every critical event can still overload a planner during a pathological storm, and no model-token/task-correctness/latency benefit is established here. Any model-facing benefit requires a separate matched integration experiment.
