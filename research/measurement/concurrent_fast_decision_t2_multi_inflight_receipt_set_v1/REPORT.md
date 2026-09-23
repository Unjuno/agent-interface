# #1469 T2 multi-inflight exact receipt-set drain

Decision: **PASS_T2_MULTI_INFLIGHT_RECEIPT_SET_SCOPED**

## Question

#1459 established scoped receipt-drain handback for exactly one in-flight local actuation. This successor changes one applicability dimension: two pre-return in-flight requests while duplicate, stale, cross-cycle, unknown, malformed, and out-of-order receipt delivery is possible.

The compared accounting policies are:

- `RECEIPT_COUNT_DRAIN`: complete handback after two syntactically valid same-cycle completion receipts, regardless of whether they identify two distinct outstanding requests.
- `REQUEST_SET_DRAIN`: snapshot the exact pre-return request IDs and remove an outstanding ID only once when its matching valid receipt arrives.

## Formal result

Frozen seed `146720260918014`; one invocation; 120,000 traces / 240,000 paired arm rows; reruns/replacements/tuning 0.

- request-set candidate post-transfer genuine completions: **0**
- count-only comparator post-transfer genuine completions: **60,000**
- candidate/oracle mismatch: **0**
- candidate incomplete handbacks: **0**
- honest candidate liveness: **30,000 / 30,000**
- duplicate-before-second-completion discriminator traces: **30,000**
- invalid/spurious receipts ignored by the candidate before completion: **90,000**
- outcome digest: `ceef82770032245eb4027fd9fe6cc77e7d8df06898bc8e68f302519b5282ef9a`

Independent audit regenerates the full deterministic corpus and passes with no errors. Four copied-result corruptions are all rejected.

## Interpretation

Receipt cardinality is not a sufficient handback-completion predicate once more than one local request can be in flight. A duplicate or stale same-cycle receipt can satisfy a count without proving that every pre-return request has completed. Binding drain state to the exact outstanding request identity set eliminates that measured escape while preserving all honest two-receipt handbacks in this synthetic contract.

This result is an applicability boundary, not a requirement to increase runtime concurrency. A runtime that permanently enforces at most one in-flight request remains covered by #1459. An implementation may encode the same invariant with generation/sequence capability tokens instead of a literal set.

## Limits

Standard-library same-process simulation only. No X11/XTEST, model/provider, GUI task, lost-receipt recovery, durable journal, cross-process clock inference, or production latency claim. Do not promote this result as evidence that multiple in-flight execution is beneficial.
