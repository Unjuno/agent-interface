# Opt-in Win32 late-input quarantine experiment

This branch adds an explicit, opt-in settle window to the supervised Win32
cancellation supervisor. `OperationCancellationSupervisor` accepts
`late_input_horizon_ns` from 0 through 60 seconds (default `0`). When positive,
cancellation stays `recovery_pending` after the first neutral readback; the
prestarted independent observer is polled repeatedly through the configured
horizon. Any non-neutral,
invalid, late, or too widely spaced sample leaves the operation `UNKNOWN` and
replay denied. New operation admission remains fenced while the old operation
is pending. Successful completion retains the horizon, sample count, time
range, and maximum observed sample gap. The public `create_server` route
accepts `supervised_win32_late_input_horizon_ns` and verifies that the owner
actually installed the requested value. Cleanup deadlines include the configured
horizon plus the existing recovery budget.

The default is still zero, preserving existing opt-in Win32 behavior until a
finite native horizon is justified. A configured window means periodic
neutral samples were observed across that duration; sampling cannot prove that
no transient occurred between observations and fake API state does not qualify
Windows `SendInput` timing.

## Retained checks

`run_results.json` preserves normal and optimized command arguments, output,
exit codes, elapsed times, Python/platform, and SHA-256 values for the runtime
and test sources. The focused suite ran 135 tests in normal mode and 135 under
`-O`; both exited 0. Key regressions:

- `ProcessCancellationTests.test_delayed_down_during_recovery_horizon_keeps_owner_fenced`
  injects an old DOWN after the first neutral readback. A subsequent observer
  sees it, leaves the old operation `UNKNOWN`, and the owner rejects the next
  generation.
- `ProcessCancellationTests.test_cancel_returns_pending_and_recovers_only_after_exact_child_exit`
  runs a 100 ms clear horizon, confirms multiple neutral observations span the
  horizon with bounded sample gaps, and only then records recovery.
- `OwnedWin32SessionTests.test_cancel_deadline_includes_configured_late_input_horizon`
  checks that the cleanup deadline covers the configured observation window.
- `SupervisedBackendCompositionTests.test_public_route_binds_requested_late_input_horizon`
  checks that the public MCP route refuses to silently ignore requested setup.

Reproduce with `py -3.11
research/integration/win32_late_input_horizon_20261028/run_checks.py`. The
runner executes each mode sequentially and rewrites `run_results.json`.

This is Windows-hosted process and shared fake-state evidence. It does not call
`SendInput`, control a real application, establish a native delayed-input
horizon, or prove MAP01/task success. No Docker workload ran; Docker Desktop's
daemon was unavailable. WSLc remains STOP/HOLD under Issue #7924.
