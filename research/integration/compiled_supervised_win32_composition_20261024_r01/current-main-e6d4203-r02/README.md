# Current-main rerun R02 — compiled graph to supervised Win32 caller

**Disposition: PASS_SYNTHETIC_COMPOSITION_REGRESSION.** The exact ten-module focused caller/composition suite used for PR #9502 was rerun on current main `e6d4203c941ab63f7c4caf51c87e5d009a62c3f6`. Current main includes two additional cases beyond the PR's recorded run: **124/124 passed** on Windows CPython 3.11.9 in normal and optimized Python.

The suite covers compiled GUI graph behavior, admission/custody/release/recovery, target-generation admission, supervised Win32 ownership, stale-generation execution guards, operation ownership, graph-to-runtime composition, and public caller cancellation/recovery/task receipt handling. Exact stdout is retained as `normal.stdout.txt` and `optimized.stdout.txt`; asyncio slow-task diagnostic lines are present in raw output and the test process exited 0 in both modes.

This is a deterministic local regression using test doubles. It is not live GUI evidence and does not demonstrate WSLc/MAP01, physical input release, independent real-app effects, matched efficiency, or broad reliability. WSLc remains STOP/HOLD in Issue #7924; this run used no WSLc/container or Docker operation.

A SHA-256 manifest covers the two raw outputs and conditions file.
