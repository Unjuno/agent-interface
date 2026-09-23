# MAP01 v12 import-graph repair R1 (Issue #1962)

This additive source audit is a successor to the infrastructure stop in #1950. It does not rerun or reinterpret the retained MAP01 allocation.

## Frozen observation

On main `5432f3aa2374753e7ab206ad5e1f3f093ac0a641`, the entrypoint
`research/doom/session_v7.py` imports `Backend,suite` from
`research/live_control/session_v8.py`. The fetched `session_v8.py` imports
`Backend as Previous,suite` from `session_v7.py` in the same
`research/live_control` directory. This is an import-name collision/recursive
resolution hazard: the doom entrypoint's intended v8 dependency is not a
self-contained import boundary.

## Disposition

`STOP_IMPORT_GRAPH_REPAIR_NOT_YET_IMPLEMENTED`. This branch records the
source identity and collision boundary only. No MAP01, GUI, model, X11,
network, or formal invocation was made. No retained evidence was changed.

The next implementation must add a private adapter/namespace under the issue's
dedicated path, run `py_compile` and an isolated import smoke in a container,
and prove that imported symbols resolve to the intended backend classes without
changing retained source or fixture hashes.
