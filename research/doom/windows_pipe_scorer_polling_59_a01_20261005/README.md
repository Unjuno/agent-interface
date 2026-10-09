# Windows pipe scorer polling A01

## H / T / D / C / U

**H:** V15's readiness loop can consume Windows redirected anonymous-pipe stdin and observe EOF without moving command dispatch or scorer sampling off the caller thread.

**T:** On the source pair pinned in `FREEZE.json`, replace the Windows `select.select` path with Windows handle waiting while retaining the non-Windows path. Exercise the complete focused polling suite, including delayed pipe input, same-owner-thread callbacks, and EOF after writer close, in normal and optimized Python.

**D:** PASS_CONSTRUCTION_PORTABILITY iff all 14 focused tests pass in both modes on Windows, including both Windows-only pipe regressions, and branch readback matches the frozen candidate blobs.

**C:** The Windows path uses `WaitForSingleObject` for character handles and a bounded `PeekNamedPipe` polling loop for pipe handles. The polling interval is 1 ms; synchronous Win32 API calls are not a hard real-time guarantee. Disk handles are treated as immediately readable. Unsupported handle types fail closed.

**U:** This is a platform portability/construction result only. It does not prove V39/V15 integration, per-key release custody, threat exposure, useful feedback, task effect, recovery, gameplay outcome, latency, or MAP01 success. No game, model, GUI, container, X server, or OS input was run.

## Result

On the Windows host (CPython 3.11), the focused suite passed **14/14** in normal mode and **14/14** with `-O`. The included raw log records each test result. The test invocation used the exact candidate source and test content later read back from the PR branch; blob identities appear in `FREEZE.json`.

The initial baseline failure remains part of the originating repository record: Windows `select.select` on an anonymous pipe raised WinError 10038. That failure motivated this bounded repair; no failed candidate run is hidden or relabeled.

Run the mechanical source and contract check with:

```powershell
python -B research/doom/windows_pipe_scorer_polling_59_a01_20261005/audit.py
```

Re-run the focused suite from `research/doom` with:

```powershell
python -B -m unittest -v test_main_thread_scorer_polling_v1
python -O -B -m unittest -v test_main_thread_scorer_polling_v1
```
