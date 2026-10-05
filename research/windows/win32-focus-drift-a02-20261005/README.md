# Win32 native foreground fence A02

## H / T / D / C / U

**H.** In a real Windows window session, if the currently focused target fixture
activates a second owned fixture between the backend's successful `focus()` and
the next key operation, the candidate session must observe the changed foreground
HWND and refuse before calling `SendInput`. Its terminal release must still
verify empty held-input state.

**T.** Use two private instances of `runtime.backends.win32_v1.fixture_app`.
After backend focus succeeds, post a test-only foreground-switch message to the
target; its foreground-owning message loop activates the decoy HWND. Run the same
test once against the frozen parent backend and once against the candidate.
`SendInput` is replaced by a call counter that returns zero if invoked, so no OS
keyboard or mouse input is emitted. Retain the machine-readable dispatch reply,
foreground HWNDs, fixture event logs, and unittest output for both runs.

**D.** Candidate PASS requires the decoy HWND to be foreground, session status
`execution_failed` with a foreground-mismatch detail, zero `SendInput` calls,
verified terminal release, no input-transition rows, and no target/decoy effect
file. Parent is expected to call the sentinel `SendInput` and fail the specific
foreground-mismatch assertion.

**C.** This is a controlled OS focus transition through two self-owned windows;
it does not model arbitrary user focus churn. A first construction attempt asked
the test harness process to activate the decoy directly. Windows denied that
request because the harness did not own foreground at that point. A second
fixture-bootstrap attempt started the target before decoy metadata existed. Both
pre-freeze outcomes are retained as setup failures; neither emitted input.

**U.** The test uses real `SetForegroundWindow`/`GetForegroundWindow` behavior
but intentionally stubs `SendInput`. It establishes a native foreground-check
refusal path, not OS input delivery, physical key state, application task effect,
the residual check-to-insertion race, or broad desktop reliability.

## Result

The baseline and candidate outcomes are in `results/a02/`. The candidate's
two-window switch was observed by the actual Win32 foreground API. The backend
refused before `SendInput`; terminal release reported verified empty state. No
application effect was created. The prior A01 synthetic test result remains
unchanged.

## Reproduction

From the repository root on an interactive Windows desktop with Python 3.11:

```powershell
$env:AI_FOCUS_DRIFT_RAW = 'research/windows/win32-focus-drift-a02-20261005/results/a02/candidate.raw.json'
python -m unittest runtime.backends.win32_v1.test_focus_drift.NativeForegroundFenceTests -v
```

The candidate test's `SendInput` replacement is a hard no-input boundary.
`FREEZE.json` binds the source files and parent backend blob. `audit.py` checks
the retained raw records, test outcomes, and source/log hashes.
