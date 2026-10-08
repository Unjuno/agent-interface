# #4114 — schema-scoped SQL dependency metadata replacement

## H
A dependency set captured once from SQLite authorizer READ callbacks can become incomplete after a view retarget. A statement-lifetime union is safe for that retarget but retains obsolete dependencies and creates false invalidations. For the frozen singleton-view family, replacing metadata when schema_version changes and then reusing it within that schema version should preserve exactly the current base-table dependency.

## T
Fresh SQLite database per case. Three policies: STALE_METADATA, LIFETIME_UNION, SCHEMA_SCOPED_REPLACE. Eight directed scenarios x two repetitions = 48 subprocess cases. The query is SELECT value,revision FROM v_dep; the view initially targets A. Schema steps cover stable A, A->B retarget, unrelated schema change, and A->B intermediate execution -> A. After final preparation, mutate none/A/B, validate the recorded dependency revisions inside BEGIN IMMEDIATE, and publish only a private effect row if validation passes. Every authorizer callback returns SQLITE_OK. Construction is excluded.

## D
PASS_SCHEMA_SCOPED_SQL_DEPENDENCY_REPLACE_SCOPED iff all 48 rows/process/source bindings audit and STALE_METADATA has missing dependency + unsafe acceptance + false invalidation; LIFETIME_UNION has no unsafe acceptance/missing dependency but has obsolete extra dependency + false invalidation; SCHEMA_SCOPED_REPLACE has zero missing, extra, unsafe and false invalidation across 16 cells; eight semantic/provenance corruption controls reject.

## C
Cooperative singleton-view SQL only. UDFs, triggers, attached/virtual tables, hidden external state and arbitrary SQL are out of scope. schema_version invalidation can be conservative. Revision maintenance is assumed correct.

## U
No production ABI, performance, model/GUI/task, crash durability, authentication or general SQL completeness claim.
