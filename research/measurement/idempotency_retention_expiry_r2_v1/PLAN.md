# #24 idempotency retention expiry R2
Task: IDEMPOTENCY-RETENTION-EXPIRY-R2-20260918-002
Base: 9d6e4b558edff90b42a416350c43b3d023d219bb
Detailed retention: valid iff query_age_ms < 1000; age >= 1000 is expired.
Factor: expired known may-have-effect identity -> ordinary NOT_FOUND vs explicit EXPIRED_UNKNOWN.
Formal: seed 240220260918002; 160000 traces; 8 families x20000; one invocation; reruns/replacements/tuning0.
