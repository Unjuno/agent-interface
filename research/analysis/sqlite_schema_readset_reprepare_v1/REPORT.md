# #4114 schema-scoped SQL dependency metadata replacement

Decision: **PASS_SCHEMA_SCOPED_SQL_DEPENDENCY_REPLACE_SCOPED**.

## First formal outcome

One frozen formal invocation completed 48/48 fresh subprocess cases with external exit 0. No reruns, replacements, pooling or post-freeze tuning. Independent raw/SQLite audit errors: 0. Eight copied-evidence semantic/provenance corruption controls were all rejected.

| policy | cases | missing dependency | extra dependency | unsafe acceptance | false invalidation |
|---|---:|---:|---:|---:|---:|
| STALE_METADATA | 16 | 6 | 6 | 2 | 2 |
| LIFETIME_UNION | 16 | 0 | 10 | 0 | 4 |
| SCHEMA_SCOPED_REPLACE | 16 | 0 | 0 | 0 | 0 |

## Interpretation

A dependency set retained forever becomes incomplete when the warm SQL view retargets A→B: the directed B mutation is missed and a stale private effect is admitted. A lifetime union closes that unsafe miss but retains obsolete A after B becomes current, and also retains B after a later B→A transition, producing conservative false invalidations.

For this frozen singleton-view family, clearing dependency metadata on a changed SQLite `schema_version`, then rebuilding it from the next recompile and reusing it only while the schema version is unchanged, exactly tracked the current base table in all 16 candidate cells. Current dependency revisions were still re-read per intent; metadata reuse was not value/revision reuse.

## H/T/D/C/U

**H:** schema-version-scoped replacement avoids both stale missing dependencies and statement-lifetime obsolete dependencies in this bounded family. Supported within the declared matrix.

**T:** three policies × eight directed schema/data schedules × two repetitions. Fresh DB/process per case; authorizer observation only; validation plus private effect publication under BEGIN IMMEDIATE.

**D:** all preregistered gates and independent audit pass; unsafe and over-invalidating controls remain explicitly rejected policies, not hidden by the candidate PASS.

**C:** cooperative SQLite singleton view; correct revision maintenance is assumed. Schema invalidation may be conservative.

**U:** no general SQL/UDF/trigger/virtual/attached-table completeness, GUI/model/task utility, crash durability, performance, production ABI or security claim. Unsupported SQL/source must remain UNKNOWN rather than dependency-free.

## Construction and provenance

Two excluded construction envelopes ended during later audit/control steps after their scientific-shaped rows had already completed. They remain construction only; poolable construction rows are 0. Exact source/decision hashes were committed and commented on Issue #4114 before formal invocation.

Formal evidence archive: `efe2a55f2b0f85bcf2921243c622c6e74f20b56a6e99fc67e3e8d9a2eb4dd0da` (22568 bytes). It contains 256 retained formal files including MANIFEST.json; the manifest itself lists 255 other files.

## Postformal packaging note

The first shell command used to emit the Base64 delivery representation had a shell-redirection syntax error after the archive, RESULT and REPORT had already been created and hashed. No scientific process was rerun. Base64 splitting and publication were performed afterward as review-only evidence transport.
