# Win32 R11 setup probe — foreground denied, state read not reached

**Disposition: `HOLD_STATE_READBACK_UNKNOWN`; no input dispatched.** A new
repository-owned Win32 fixture was created on current main
`1b1ce38c943a5f93d94e6a9f028f5a50ceed618b`. The fixture was visible, but the
foreground handle after its own startup activation did not equal the fixture
HWND. An explicit parent-process `SetForegroundWindow` call returned false and
the foreground remained unchanged. The probe then failed to import `runtime`
because the probe script did not add the repository root to `sys.path`; native
key-state readback was not reached.

The fixture emitted only its `ready` event, no effect file, and exited with code
0. Cleanup restored the foreground value sampled before launch. The frozen
pretrial manifest has four entries with zero mismatches; the raw-run manifest
has five entries with zero mismatches. The stop audit records a clean
pre-input exclusion, not a recovery result.

## Next adjustment

Use Computer Use to activate the exact fixture window, then verify its HWND is
the foreground window. Fix the diagnostic probe's repository import path. A new
attempt must separately record activation outcome and native SHIFT readback;
keep R11 immutable. Do not dispatch recovery input until the native read is a
boolean neutral state with a valid witness.
