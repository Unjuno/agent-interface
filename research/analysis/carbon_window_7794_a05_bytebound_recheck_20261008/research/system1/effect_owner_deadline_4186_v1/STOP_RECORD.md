# Issue #4195 formal execution STOP

Disposition: **STOP_EXTERNAL_EXECUTION_TIMEOUT**.

The prospectively frozen allocation `effect-owner-deadline-4195-20260923-01` was invoked exactly once with the registered command. The outer execution tool terminated the invocation at its 45-second envelope before `run.py` serialized `formal/ROWS.json`.

- expected formal rows: 36
- complete retained `row.json`: 9
- partial case directories without `row.json`: 1 (`formal-0-APP_CHECK_ONLY-NEAR_LONG`)
- formal reruns/replacements/tuning: 0 / 0 / 0
- formal audit/controls: not run because the denominator is incomplete
- source freeze recheck before invocation: PASS

This is an execution-envelope STOP, not `PASS_EFFECT_OWNER_DEADLINE_SCOPED`, not a scientific FAIL, and not permission to rerun the consumed allocation under the same identity. Preserve construction and the partial first outcome. Any fresh allocation needs a separately frozen identity/envelope under this same scientific question unless the question itself changes.
