# Win32 orphan recovery without target foreground (2026-11-15)

## Finding

The Win32 backend contract in `runtime/backends/win32_v1/README.md` documents global key/button UP and `release_all` cleanup that can run without a foreground target. However, `OperationCancellationSupervisor.recover_orphaned_input` requested `focus_target_before_release=True` for automatic orphan recovery. That made foreground refusal block a generation-checked cleanup path even though foreground is not needed to send UP events. This is relevant to the R269 postrun custody: a prior same-generation recovery attempt failed foreground verification. R269 itself remains unresolved; this change does not retry or adjudicate that operation.

## Candidate change

Automatic orphan recovery now requests foreground-free release (`focus_target_before_release=False`) while retaining operation/recovery IDs, source and target generation checks, bounded deadline, typed release receipt, independent neutral-state observation, and UNKNOWN on uncertain outcomes. The helper regression asserts no focus event and verifies key-up/release receipt. The supervisor regression exercises the actual `recover_orphaned_input` path and checks both release and observer requests are foreground-free. Explicit focus behavior remains covered by existing opt-in/focus-refusal tests.

## Verification

On CPython 3.11.9, the combined cancellation + native-helper core suite passed 74/74 normally and 74/74 under `python -O`. The public MCP fresh-generation recovery query passed 1/1 normally and 1/1 under `-O`.

An earlier combined three-module run passed 120/120 normally. Its `-O` run had one failure in the existing timing-sensitive `test_blocked_independent_observer_expires_unknown` at its 2-second observer-start wait. The test passed individually in normal and optimized mode and the later core/public split suites passed both modes. The initial failure is retained as a timing flake signal; no test thresholds were changed.

Logs are preserved in `D:\CodexData\Workspaces\2026-11-15-agent-interface-followup\`: `core-normal.log`, `core-optimized.log`, `public-query-normal.log`, `public-query-optimized.log`, plus earlier `win32-focus-free-recovery-20261115.normal.log` and `.optimized.log` from the combined run.

## Scope and next gate

This is a local protocol/helper regression result, not a native GUI experiment, proof of MAP01 task effect, or an efficiency comparison for #57. Do not replay R269's operation/generation. A live successor requires a separately authorized fresh operation/generation and a suitable target/foreground condition. The candidate is based on current main `58bd28b00d18dbc2c8a886f4b6b7f064b6ec19b2`.
