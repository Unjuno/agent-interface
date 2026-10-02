# T11 integration qualification

T11 is retained as an immutable historical finite-model result, not as the canonical schema-safe record. Its original `FREEZE.json`, source, raw rows, audit, and `REPORT.md` are preserved unchanged.

The later, separately frozen T12 successor is the canonical strict-scope record: [`gluing_numeric_schema_5537_t12_v1/`](../gluing_numeric_schema_5537_t12_v1/). T12 added machine-readable observed-subgraph-only scope for incomplete evidence, omitted full-cover minimax/witness claims when context is missing, and added strict schema/type checks (including bool/int alias mutations). T12 did not retroactively repair, upgrade, or alter T11.

Therefore:

- T11's 144-row result and six mutation controls remain evidence only for its frozen finite numeric model and stated complete-case/policy checks.
- T11 did not serialize the incomplete-subgraph minimax/witness scope as strictly as T12, and its auditor did not establish T12's strict malformed-schema/type rejection boundary.
- Use T12 when citing the repository's strict-schema and incomplete-scope result. Do not combine T11 and T12 counts or present T11 alone as satisfying T12's stronger boundary.
- Neither result establishes calibrated real-world tolerances, general sheaf solving, live GUI evidence validity, runtime safety, or product behavior.

This note is additive qualification; it does not modify or rerun either frozen experiment.
