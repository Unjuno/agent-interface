# MAP01 v12 import-graph repair R1 (Issue #1962)

This additive source audit is a successor to the infrastructure stop in #1950. It does not rerun or reinterpret the retained MAP01 allocation.

## Corrected frozen observation

On the historical audit base `main@5432f3aa2374753e7ab206ad5e1f3f093ac0a641`,
the Doom entrypoint inserts `research/live_control` at `sys.path[0]` and
imports bare `session_v8`. That module's bare `session_v7` import correctly
resolves to `research/live_control/session_v7.py` in the intended fresh
process. The observed circular import instead occurs when the Doom file
`research/doom/session_v7.py` is loaded under the top-level name
`session_v7`; its partially initialized module then captures
`sys.modules['session_v7']` and is re-entered by `session_v8`.

## Disposition

`STOP_IMPORT_GRAPH_REPAIR_NOT_YET_IMPLEMENTED`. This branch records the
corrected source identity and collision boundary only. No MAP01, GUI, model,
X11, network, or formal invocation was made. No retained source or historical
evidence was changed.

The next implementation must repair or isolate the Doom entrypoint's module
identity under the dedicated path, run `py_compile` and separate import-only
smokes for the intended and failure-triggering load paths in a container, and
prove that imported symbols resolve to the intended backend classes without
changing retained source or fixture hashes.
