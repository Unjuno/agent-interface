# Allocation 02 orchestration delta

Scientific H/T/D/C/U and 48-row + 4-control gates remain exactly PLAN.md / Issue #4236.

Changed execution factors only:
- allocation id `predicate-cache-persist-4217-20260923-02`;
- three immutable repetition batches instead of one monolithic runner;
- each candidate subprocess uses `python -S -B` (stdlib-only source, avoiding unused site startup);
- each formal batch owns exactly one repetition: 8 cases × 2 policies = 16 rows; batch 2 also owns the four malformed-artifact controls;
- `aggregate_v2.py` combines only three complete batch files into FORMAL_V2.json and executes no candidate logic;
- audit and corruption controls run read-only after aggregation.

Each formal batch is invoked exactly once. A missing/nonzero/incomplete batch stops allocation 02. Never rerun a consumed batch or substitute allocation-01 rows. Construction uses two cases under a separate construction output and is excluded.
