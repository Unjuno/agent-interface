# Golden IPC transitive closure v2 (#2922)

This additive gate updates the provenance audit after the flat-import shims merged in #2943 and #2948. It does not modify or rerun #2813, #2705, or #2730 results.

The gate checks that each historical flat import has an explicitly declared canonical source and that both the shim and canonical file exist. It does not execute X11, Docker, model IPC, GUI/input, or task effects.

Decision vocabulary:

- `PASS_STATIC_CLOSURE_DECLARED`: all declared paths exist and the manifest is internally consistent.
- `STOP_STATIC_CLOSURE_MISSING`: a declared shim or canonical source is absent.
- `HOLD_RUNTIME_READY_UNVERIFIED`: static closure passes but no runtime ready event has been produced.

A static PASS is not a runtime or task-success claim.

## CI evidence boundary

The dedicated workflow runs this static verifier on pull requests touching the closure paths. A green workflow proves only declared filesystem closure; it does not prove runtime readiness or task execution.
