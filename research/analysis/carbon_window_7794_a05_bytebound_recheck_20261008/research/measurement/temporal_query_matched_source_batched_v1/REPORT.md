# #1501 Batched matched-source temporal query preflight — retained result

Decision: **PASS_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED_SCOPED**

- Formal histories: 220,000 in 20 immutable batches of 11,000.
- Candidate/oracle mismatches: 0.
- Total leakage counters: 0.
- Fixed coverage: 26.024%.
- Queryable coverage: 91.383%.
- Matched-source advantage: 65.359 percentage points.
- Query worse classes: [].
- Independent audit: PASS.

Class breakdown:
- EVENT_CENTERED: fixed 0.000%, query 99.980%, delta 99.980 pp (n=55,000).
- LONG_BASELINE: fixed 100.000%, query 100.000%, delta 0.000 pp (n=55,000).
- RECENT_DENSE: fixed 0.000%, query 65.551%, delta 65.551 pp (n=55,000).
- REVERSAL_BRACKET: fixed 4.096%, query 100.000%, delta 95.904 pp (n=55,000).

Interpretation: this is a model-free source-matched selection-mechanics PASS. It shows that when the temporal relation is revealed only after retention, bounded query selection can retrieve relevant time relations from the same immutable history/budget more often than one frozen schedule. It does not show that a frontier model benefits, nor task correctness, token savings, wall-clock speedup, GUI transfer, or production readiness. Rung2 model work must preserve matched source capability and total evidence budget.
