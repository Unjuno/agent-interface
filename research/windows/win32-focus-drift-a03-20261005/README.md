# Win32 native foreground fence A03

This is a fresh paired construction after A02 stopped before candidate or
baseline startup because its source materializer requested a nonexistent
`runtime/__init__.py`. A03 omits package initializer files and materializes only
the exact parent runtime modules required by Python namespace-package imports.
The A02 STOP is preserved unchanged. The paired result is in [`RESULT.md`](RESULT.md).

## H / T / D / C / U

**H.** With two private fixture HWNDs, a foreground target window can activate a
decoy after the Win32 backend reports focus success. The candidate must detect
the changed real foreground HWND and refuse before `SendInput`; release cleanup
must still verify empty state.

**T.** Run one exact-parent baseline and one candidate test with the same
candidate-only fixture switch and test source. A foreground-owning fixture
message loop asks Windows to activate the other fixture. The test replaces
`SendInput` with a call counter returning zero, so neither run emits OS input.
Each writes a JSON dispatch record plus unittest stdout/stderr.

**D.** Candidate PASS requires actual decoy foreground, `execution_failed` with
`foreground focus changed`, zero `SendInput` calls, verified empty release, no
input-transition rows, and no effect file. Parent should call the sentinel and
fail the foreground-specific assertion. Any foreground-switch failure or
missing raw record is HOLD/STOP, not a negative control.

**C.** The windows are private test fixtures and the switch is a controlled
message, not natural user focus churn. A02 remains STOP because baseline source
preparation failed; its allocation is not retried.

**U.** This exercises real foreground APIs and the actual session dispatch path.
It does not test global input delivery (the API is stubbed), physical key state,
task effects, the check-to-insertion race, or broad desktop reliability.

## Reproduction

On Windows with Python 3.11, from the repository root:

```powershell
python research/windows/win32-focus-drift-a03-20261005/prepare_baseline.py . research/windows/win32-focus-drift-a03-20261005/results/a03/baseline-source
$env:AI_FOCUS_DRIFT_RAW = 'research/windows/win32-focus-drift-a03-20261005/results/a03/baseline.raw.json'
python -m unittest runtime.backends.win32_v1.test_focus_drift.NativeForegroundFenceTests -v
```

Run the unittest command once from `results/a03/baseline-source` with
`AI_FOCUS_DRIFT_RAW` set to `baseline.raw.json`, and once from the repository
root with it set to `candidate.raw.json`. The exact source and commands are in
`FREEZE.json`. `audit.py` checks source hashes and both retained outcomes.
`POSTRUN_SOURCE_INVENTORY.json` adds exact Git blob IDs for the baseline's
backend/session/contract source closure. It was added after execution for easier
reconstruction and does not alter the frozen protocol or decision rule.
`POSTRUN_CANDIDATE_GIT_BLOBS.json` records raw Windows source hashes and the
CRLF-to-LF Git normalization; the audit verifies normalized bytes equal staged
blobs.
