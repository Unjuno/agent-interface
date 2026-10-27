# A07 owner-release error-field successor

This synthetic-only successor copies the A07 owner-release reconciliation and requires both `keyrelease_error` and `sync_error` fields to be explicitly present and null when counting a terminal key-up attempt. Previously `dict.get` treated absent fields as null: two separate missing-field mutations falsely returned `PASS_CUSTODY_RECONCILED_SCOPED`. The pre-existing terminal-cleanup positive fixture remains supported.

Run `python -B -m unittest test_audit_a07_owner_release_reconciliation test_missing_attempt_errors -v` in this directory, and repeat with `-O`. Six tests pass in each mode. No historical A07 data or output was read or changed. This is not a live GUI, physical release, task-effect, or formal-pass result. It does not resolve the separately identified v3 admission/release identity mismatch or prove all owner-release integrity checks complete.

A second synthetic regression establishes that a failed attempt followed by a clean attempt must not be promoted by filtering out the failure. This conservative gate requires all attempts in the terminal cleanup evidence to satisfy the frozen checks. It may hold cases that later evidence could disambiguate. Seven tests pass normally and under optimized Python.

The keymap-before and keymap-after error fields must also both be present and null: synthetic error and missing-field mutations fail closed. This uses the current owner receipt schema; legacy records without these fields are not promoted. Eight tests pass normally and under optimized Python. No saved A07 audit was rerun.
