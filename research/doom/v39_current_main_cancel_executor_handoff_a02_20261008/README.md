# V39 cancel/release handoff replay: current-main source alignment A02

## H / T / D / C / U

**H.** The retained A01 cross-layer replay uses source modules whose exact Git blobs still occur in current main: the V39 cancel helper, planner adapter, App Server client, and all nine ExecutorV13 stack modules. An isolated rerun against those byte-identical sources preserves the release-before-interrupt-response ordering.

**T.** Freeze current main `2a9052efdd155b8cdc173d216a969ea5f64a1ce9`. Compare the 13 source Git blob identities in A01's freeze against that commit. Copy A01 to a temporary directory on the same volume, then execute its candidate, unittest, and independent source/event auditor there so its retained historical `RESULT.json` and `AUDIT.json` remain untouched.

**D.** PASS only if all 13 blobs match, candidate and unit test return zero, the independent A01 audit passes, and the event sequence remains cancel write/flush → interrupt request → input release → verified empty terminal → interrupt response.

**C.** This is a software composition replay with an in-memory owner and a withheld simulated response. It checks source alignment and a single controlled ordering only.

**U.** Matching Git blobs establish current-main source identity, not that the simulated stack is the live production deployment. No OS-level physical key release, actual game, live threat exposure, production timing, useful application feedback, recovery, or task effect is tested.

## Result

See `RESULT.json` and the retained command outputs. The A01 evidence remains unchanged. This addendum only strengthens the provenance of the existing software-composition result; it does not satisfy Issue #59's live threat-exposure gate.

Two setup failures are retained in `DEVELOPMENT_FAILURE_01.txt` and `DEVELOPMENT_FAILURE_02.txt`. The first run used the full C: temporary volume and stopped before the candidate due to no free space. The first isolated replay then exposed that A01's legacy candidate rewrites `RESULT.json` with Windows newline bytes before its manifest auditor runs. A02 now directs temporary files to its D: workspace, restores the frozen RESULT bytes inside the temporary copy, and audits only after restoration. Neither setup failure was a control-mechanism outcome.

## Reproduction

From repository root, run:

```powershell
python -B research/doom/v39_current_main_cancel_executor_handoff_a02_20261008/run_replay.py
python -B research/doom/v39_current_main_cancel_executor_handoff_a02_20261008/verify.py
```

The replay runner copies A01 into a temporary directory under this A02 package before executing it.
