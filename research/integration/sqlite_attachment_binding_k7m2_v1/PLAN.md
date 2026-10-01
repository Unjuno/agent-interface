# #4360: attached-database lifetime and dependency reuse

## Scope and roadmap
Parent #4088/#4114, broad #1713. This changes the previously excluded ATTACH/DETACH lifetime, not the consumed 60-case cache study or owned single-database reprepare allocation. New comparison implementation only; no production SQLite/authorizer defect is alleged. Every authorizer returns SQLITE_OK.

Roadmap: inspected current main/Issues/PRs/branches -> excluded 16-case construction -> public exact source/gate freeze -> four immutable 8-case batches -> independent raw/database audit and eight effective mutations -> complete additive evidence PR -> applicable exact-head checks and qualified merge/readback. Only this owned branch may be considered for cleanup; broad ROADMAP stays open.

Intake main: 4a1f3957e91b412a64769199f78f2c4b0102d28b. Issue: 4360. Branch: research/sqlite-attachment-binding-20260925-k7m2. Path: research/integration/sqlite_attachment_binding_k7m2_v1/. Bounded search is not knowledge of unpublished work. Earlier conversation artifacts are unchanged and not copied into the formal denominator.

## H
Schema counters are database-local, not unique database identities. Independently created A and B can each have schema_version 3 while their same-named view uses different base tables. A connection/alias/SQL/schema counter cache may therefore retain the wrong dependency after alias replacement. Owner-maintained, monotone, per-alias attachment generation should invalidate metadata and prepared receipts at that boundary without rejecting an unrelated alias replacement.

## T
Fresh main/A/B/U databases per case; A and B each have alpha, beta, v_dep. A view selects alpha; B selects beta. No assignment to schema_version. All alpha rows start (a0,1), beta rows (b0,1). All effects are private main.effects rows. DELETE journal/default synchronous FULL, explicit BEGIN for preparation and BEGIN IMMEDIATE for validation plus effect. Separate persistent reader and writer/observer peer processes communicate through bounded JSON-line pipes. Reader alone owns its connection/attachments; no concurrent attach during validation. Logs contain exact request/reply bytes, SQL and callbacks; final database files are retained. Audit opens these files read-only and imports no candidate/driver.

SCHEMA_ONLY reuses dependencies within the same alias/SQL/schema counter, even when a new callback describes another source. BINDING_SCOPED also keys metadata by attachment generation and validates the prepared generation. This comparison deliberately extends the scoped concept to a previously excluded source family; it does not assert that #4114's implementation promises attached-database support.

Eight scenarios, two policies, two repetitions =32 cases, in lexicographic declared scenario order, repetition0 then1, SCHEMA_ONLY then BINDING_SCOPED. Batches0..3 own consecutive eight-case ranges. All gates frozen after excluded construction, before first formal case. Stop on source/process/timeout/missing evidence. No same-batch retry, replacement, pooling or post-freeze tuning. Connection setup retries: none. Response bound3s, child-exit bound3s, foreground batch supervisor25s, outer call40s. Timings are diagnostics, not measurements of benefit.

| Scenario | SCHEMA_ONLY | BINDING_SCOPED |
|---|---|---|
| STABLE | accept a0 | accept a0 |
| CURRENT_WRITE | refuse alpha revision change | same refusal |
| UNRELATED_WRITE | accept a0 | accept a0 |
| REBIND_PRE | accept b0 with obsolete alpha dependency | accept b0 with beta dependency |
| REBIND_PRE_CURRENT_WRITE | stale b0 effect | refuse beta revision change |
| REBIND_PRE_OLD_WRITE | false refusal from alpha | accept unchanged b0 |
| REBIND_POST | stale a0 effect against B | refuse binding change |
| OTHER_ALIAS_POST | accept a0 | accept a0 |

## D
PASS_ATTACHED_DATABASE_DEPENDENCY_BOUNDARY_SCOPED requires complete32-case/four-exit/source/IPC/DB evidence, independently reconstructed table above and all8 effective well-formed semantic mutations rejected without auditor crashes or no-ops. Expected totals per16 cases: SCHEMA_ONLY missing6/extra6/stale4/false-refusal2/accepted12/refused4; BINDING_SCOPED missing0/extra0/stale0/false-refusal0/accepted10/refused6. A complete contradiction is FAIL at the registered gate; infrastructure/coverage uncertainty is STOP/HOLD. The baseline remains rejected, not rescued by the boundary-study PASS.

## C and U
A cooperative owner must mediate every attachment change and preserve generation monotonicity; a raw untracked rebind is out of contract. All relevant table updates must increment revisions. Fixed singleton views only; arbitrary SQL, row-level precision, functions, virtual tables, hidden external state, filesystem replacement, rollback of generations, multiple connection owners, cross-file power-loss atomicity and GUI effects are excluded. Reattaching the same file can be conservatively invalidating. A supported query/generation is not action authority, source authentication, model viewing or task success. No performance, token, natural failure-rate, Docker/OrbStack/image-attestation or product claim. Independent audit means separately coded/process-isolated, same author, not external human review. No calibrated combined uncertainty or coverage factor is assigned to this deterministic count study.

## Variables / units
| Name | Meaning | SI unit | Definition and range | Type |
|---|---|---|---|---|
| alias | connection-local database name | not applicable | slot or other | identifier |
| binding | attachment lifetime version | 1 | owner increments after successful bind; positive integer, no reuse | integer scalar |
| schema | schema change counter | 1 | read-only PRAGMA on attached DB; equals3 in this fixture | integer scalar |
| SQL | exact fixed query | not applicable | SELECT value,revision FROM slot.v_dep | string |
| dependencies | tables required by prepared query | not applicable | subset of alpha,beta, each paired with revision | finite map |
| revision | table value update counter | 1 |1 initially,2 after one controlled mutation | integer scalar |
| value | query/effect value | not applicable | a0,b0, or either with ! suffix | string |
| start_ns,end_ns | same-process monotonic RPC brackets | s (stored ns) | nonnegative increasing diagnostic timestamps | integer scalar |
| missing,extra,stale,false_refusal | finite discrepancies | 1 | exact nonnegative counts over declared cases | integer scalars |

## Conditional reasoning / unit check
A schema counter comparison is meaningful only within a source identity: equality of two local integers cannot prove equality of their owners. A and B furnish a construction with equal counter and different view definitions.

Under BINDING_SCOPED, a new slot generation gives a different metadata key, so the new compilation's observed singleton dependency replaces the prior one. Preparation samples its value and revision in one transaction. At commit, the same owner first holds the write transaction; no alias mutation occurs there. Changed binding or schema refuses. With unchanged binding/schema and complete metadata, unchanged dependency revision plus the disciplined writer rule implies the prepared value remains the current value. Thus an accepted private effect matches the current singleton result. A different alias changes neither the slot generation nor its actual dependencies, so it need not invalidate. These implications fail if any stated completeness/owner/version premise fails; no theorem about arbitrary SQL follows.

Counter/version equality and discrepancy counts are dimensionless; no comparison mixes SQLite counters with timestamps. Stored nanoseconds are never used as versions or as calibrated latency evidence.

## Primary background
- SQLite ATTACH DATABASE: https://www.sqlite.org/lang_attach.html
- SQLite schema_version PRAGMA: https://www.sqlite.org/pragma.html#pragma_schema_version
- Compile-time authorizer: https://www.sqlite.org/c3ref/set_authorizer.html
- SQLite transactions: https://www.sqlite.org/lang_transaction.html
