# Partial-input recovery: current-main conformance boundary

Date: 2026-11-03  
Current main: `473ef8431a76ba85c6da5c48fcdb6f79b2208ea3`

## Evidence lineage

The retained A02 experiment in
[`wslc_calc_partial_input_recovery_20261031`](../wslc_calc_partial_input_recovery_20261031/README.md)
ran against runtime commit `9aa43cfd2cf7edc59f5ebebd4f5b5afcbbb389a1`,
which is an ancestor of current main. Its frozen manifest has 305 runtime
files. Comparing each manifest digest with the exact Git blobs at current main
finds 4 unchanged blobs and 301 changed blobs; 52 of the pinned files belong to
the Win32 backend, guarded Win32 adapter, CLI caller, or compiled GUI core, and
all 52 have changed. There are no missing paths. This is a source-lineage
difference, not evidence that the old A02 run failed or that the current code
regressed. The A02 behavior must not be described as current-main validation.

Reproduce the comparison from the repository root:

```powershell
python research/integration/wslc_calc_partial_input_current_main_20261103/audit_runtime_lineage.py --ref HEAD
```

## Current composed-path check

Added `test_uncertain_dispatch_with_verified_release_stops_before_effect_or_replay`
to `runtime/guarded_win32_v1/test_compiled_core_composition.py`. It uses the
actual Win32 `MoveBridge` and compiled GUI core, lets the backend perform the
guarded operation and verified release, then supplies a caller's
`delivery_uncertain` status with `input_dispatched=true`. The result must retain
the reported dispatch and verified release, return `SAFE_YIELD`, record zero
completed transitions, make no subsequent observation/action, and skip task
effect verification. This catches accidental promotion of an uncertain operation
into a success or an in-run replay.
The test models the uncertain caller receipt boundary; it does not inject a
multi-emission text-entry failure or test post-obstruction recovery.

The focused compiled-core, Win32 composition, and supervised Win32 caller tests
passed: 41 tests under Python 3.11, both normally and with `python -O`.

## Scope still open

The new check establishes the stop boundary for one composed Win32 path. It does
not implement or validate automatic recovery after the obstruction clears,
fresh model grounding, an independent saved-file scorer, a persistent-input
neutral readback across a second owner, broad recovery reliability, efficiency,
WSLc allocation economics, or MAP01. Those remain separate evidence gates.
