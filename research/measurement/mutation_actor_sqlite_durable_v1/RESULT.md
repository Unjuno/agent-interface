# Result — #1233 durable SQLite mutation attribution

Decision: **PASS_MUTATION_ACTOR_SQLITE_DURABLE_SCOPED**.

- One formal invocation; reruns/replacements/tuning 0.
- 720 fresh SQLite databases across 9 case families × 80.
- 640 child-process committed mutations; cleanup 640/640.
- SQLite `integrity_check`: 720/720 `ok`.
- Candidate / independent durable-event oracle mismatch: 0.
- Lineage-bound non-self false self-credit: 0.
- Frozen 500 ms temporal-nearest false self-credit: 560.
- Authority promotions: 0; task-success promotions: 0.
- Formal record digest: `ed0c787198700d0d3cca1ebff7602af7e62e1c6c3ad79a1f026aba12bc8d16c3`.

This transfers the attribution contract from IPC messages to transactionally committed shared state + event history. It does not establish authenticated human/OS identity or real GUI/application actor detection.
