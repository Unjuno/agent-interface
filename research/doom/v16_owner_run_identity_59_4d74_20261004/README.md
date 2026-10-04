# V16 scorer-to-owner run identity (Issue #59)

Current main assigned `run_id` to V16 scorer samples, while owner admission
and release telemetry emitted by the V15 backend had no shared run identity.
That prevented a downstream reducer from distinguishing owner rows belonging
to this scorer session from rows belonging to another session.

This change carries V16's generated `run_id` through V15 into the selected
release-batch backend. The backend adds that identity as both `run_id` and
`session_id` to emitted telemetry rows without mutating the row supplied by
the owner. `session_id` matches the current occurrence reducer's join field.
Calling V15 without a `run_id` preserves its existing backend selection and
row shape.

## Verification

- The new backend identity assertion failed before the implementation because
  the backend did not accept `run_id`.
- Focused session/backend suites pass 48/48 on Windows Python 3.11 and Ubuntu
  WSL Python 3.12, including scorer acknowledgement, progress clock, V15/V16
  finalization, explicit key-up receipts, and release-batch composition.
- `py_compile` and `git diff --check` pass.

## Limits

This verifies source-level identity propagation with deterministic test owners.
It does not execute V16 against ViZDoom, admit a real key, establish application
consumption or causal effect, emit a runtime semantic-action binding, measure
physical release, or qualify recovery. The separate live MAP01 allocation
remains unresolved.
