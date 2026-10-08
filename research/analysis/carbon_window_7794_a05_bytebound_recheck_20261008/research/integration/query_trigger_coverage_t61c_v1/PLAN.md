# #4394 — query revision instrumentation lifetime

Base 4c701cc51b06296268ad8d9ae3eff1dd6f2d379d. Own only research/integration/query_trigger_coverage_t61c_v1/. Allocation t61c-20260926-01; Tokyo calendar date, raw UTC retained. No previous formal allocation is rerun.

H: current trigger-definition equality does not prove uninterrupted query-revision coverage. DDL history matters when the instrumentation itself may change.

T: 9 conditions x3 policies x2 repetitions =54 fresh SQLite databases; separately executed reader/writer processes; nine first-outcome six-case batches. Exact inherited schema.sql, fixed tenant A empty query, insertion payload9. Conditions and order are in src/runner.py. Repetition0 order REVISION_ONLY/CURRENT_DDL/SCHEMA_COOKIE; repetition1 reversed. Construction uses repetition1-count runs and is excluded. Actor3s, supervisor25s, outer tool40s. Stop on any incomplete batch, preserve partials and real exit. No replacements/reruns/pooling/tuning.

D: all54 cases/108 actors/nine batch exits and independently reconstructed sources/DB/IPC must reconcile. REVISION_ONLY stale stores6; CURRENT_DDL stale stores2; SCHEMA_COOKIE stale stores0 and conservative refusals4. Both definition-checking modes refuse two missing-at-prepare cases. Stable, unrelated-tenant and rollback controls proceed; normal relevant writes refuse. Eight effective well-formed raw-evidence controls must reject with intact-baseline PASS. Full source/gates are to be public and read back before batch0. Complete contradiction is FAIL; missing evidence is HOLD/STOP. A scoped PASS rejects the weak policy, not the documented database contract.

C: same private DB identity, ordinary DDL only, no cookie/epoch reset or wrap, known correct initial trigger SQL, no attachment/TEMP/UDF/native write bypass, no concurrent schema change within an SQLite transaction. Private effect rows only, not GUI/OS input or external actions. schema_version is a test mechanism, not a recommended general application fence. Unrelated DDL causes conservative refusal.

U: no production/model/GUI/latency/token/power-loss/natural-rate/authentication claim. Same-author separately implemented raw auditor is not external human review. Counts/bytes/order determine outcomes; clocks are diagnostic. No calibrated combined uncertainty or coverage factor is inferred.

## Variable and unit table

| Symbol | Japanese meaning | SI unit | Definition | Range / assumptions | Type |
|---|---|---|---|---|---|
| Q | 固定検索の結果 | 1 | tenant A, active=1, ordered id/payload/revision rows | finite ordered tuples | sequence |
| e | 範囲世代 | 1 | scopes.epoch for A | nonnegative integer, no reset/wrap | integer scalar |
| c | schema世代 | 1 | read-only PRAGMA main.schema_version | integer, ordinary DDL, no reset/wrap | integer scalar |
| T | トリガー定義集合 | 1 | ordered name/SQL pairs for items | exact known initial schema contract | sequence |
| p, v | 準備・検査時点 | s | logical transaction observation endpoints | p precedes v, same database | ordered instants |

All comparisons and case counts are dimensionless; diagnostic monotonic_ns brackets are nanoseconds and never mixed with database versions or used as event-completion estimates.

## Roadmap

Prior raw-only verification -> excluded construction -> public exact freeze ->54 first outcomes -> independent audit/eight controls -> full source/raw evidence PR -> applicable exact-head checks/review -> qualified merge/main readback. Global #1713/#2789/ROADMAP stays open. Keep setup/publication repairs under this same Issue.
