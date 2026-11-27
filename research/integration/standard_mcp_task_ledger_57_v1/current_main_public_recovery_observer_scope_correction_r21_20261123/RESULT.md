# R21 — scoped observer correction, long TEMP path

## Result

The one-shot/non-supervised observer lookup was restored; server binding remains only on the supervised-win32 observation branch. The combined ordinary and supervised MCP modules ran once per mode using a dedicated TEMP directory nested below the long worktree path.

Both runs executed 94 tests and failed only `test_portable_stdio_runs_outside_checkout` with `NotADirectoryError [WinError 267]` while the test tried to launch a child process from its deep temporary artifact path. Normal and `-O` each exited 1 (119.961 s and 119.479 s). The other 93 tests passed in each run.

## Interpretation

The failure is attributable to this experiment's long TEMP path exceeding Windows child-process path handling, not to observer binding. Preserve this run as an infrastructure failure. R22 changes only the TEMP root to a short C: path and is a fresh bounded validation; R21 is not retried.
