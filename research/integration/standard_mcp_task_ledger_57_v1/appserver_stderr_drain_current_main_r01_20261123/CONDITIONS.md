# App Server stderr drain current-main R01

## Frozen regression

- Main source revision: `07c0d7f72bf19d0dc2690bc01a114e0912b20f87`.
- Host: Windows 11, CPython 3.13.14.
- Target: `research.live_control.test_appserver_stderr_backpressure_current_main_r01.AppServerStderrBackpressureCurrentMainTest.test_large_invalid_stderr_does_not_block_rpc_and_keeps_bounded_raw_tail`.
- A real local child process writes 1 MiB of binary stderr, including non-UTF-8 bytes, before reading one JSON-RPC request and returning a response.
- Pass only if the response arrives within 2 seconds, close retires within 3 seconds, and the client reports the exact 1 MiB byte count, complete EOF, no read error, and the exact 65,536-byte raw tail.
- The fixture invokes no real App Server, provider, GUI, Docker, WSL/WSLc, or external allocation.
- RED phase must fail specifically because stderr backpressure prevents the RPC response. Preserve unexpected setup failures separately.
- Frozen test source SHA-256: `99ba6a70fe693bc4dbbfbfe2c26804bb5197b50fab80c05304403d1748fe223f`.
- Frozen production source SHA-256 before repair: `edd0aa2f50fed1ca941c0ffd7c099bdd3f3a9d11425b33dd190cfd39cdc56f17`.
- RED command: `py -3.13 -B -m unittest research.live_control.test_appserver_stderr_backpressure_current_main_r01.AppServerStderrBackpressureCurrentMainTest.test_large_invalid_stderr_does_not_block_rpc_and_keeps_bounded_raw_tail -v`.
- RED observed: exit 1 after 2.022 s with `TimeoutError: app-server request timed out: stderr/probe`, the predicted backpressure failure. The fixture process was reaped during test cleanup. Captured stdout, stderr, and exit code are in `raw/red-normal.*`.

## Close ownership regression

- A second frozen test checks that `close(timeout=0.1)` does not close a stderr stream while its reader is blocked on an inherited writer held by an orphan child. It must return a bounded `TimeoutError`, leave stderr open, and complete successfully when the writer exits.
- During this test's RED check, the drain-reader change was present but the close-join block was temporarily removed. `raw/red-close-sync2-normal.*` records the expected assertion `close blocked while closing a stream still owned by its reader` (1 test, 0.415 s). Two earlier harness failures (`red-close-normal.*`, `red-close-sync-normal.*`) are retained but are not counted as valid RED evidence; the fixture was corrected to wait for stdout reader retirement and to avoid inheriting stdout.
- Final GREEN source includes both the independent drain and bounded close join. The complete two-test module passed in CPython 3.13.14 on Windows in normal mode (0.262 s) and optimized mode (0.276 s); clean raw logs are `raw/green-post-cleanup-normal.*` and `raw/green-post-cleanup-optimized.*`. An earlier preliminary green run emitted a test `ResourceWarning` for an unclosed PID file; that fixture was corrected and the final runs are clean.

## Existing contract regression

- Related App Server protocol modules: normal and optimized each ran 81 tests, passed, 10 skipped by existing platform guards. Raw logs are `raw/related-clean-normal.txt` and `raw/related-clean-optimized.txt` (exit codes alongside them). The command used explicit `PYTHONPATH` for the repository root and `research/live_control`.
- The wider native protocol suite was also attempted. It ran 713 tests in 61.055 s and reported 31 errors, 3 failures, 17 skips. Many errors are Windows incompatibilities in existing POSIX `fcntl`/`O_*` tests; three failures include two MCP relay cases blocked by missing `mcp==1.30.0`, and one relay pending-resume expectation. The output log is `raw/native-suite/protocol.stderr.log`.
- The native runner then raised `UnicodeEncodeError` while printing its captured UTF-8 log through the host's cp932 console, before writing its summary JSON or starting later suites. This run is recorded as incomplete/FAIL, never as a pass. One exploratory command also included a nonexistent module and is preserved as `raw/related-normal.txt`; it is not the clean targeted run.

## Limits

- These are deterministic local fake-child protocol tests and compatibility checks. No real App Server/provider, model, GUI, task-success effect, or recovery reliability is measured. They do not close Issue #57's integrated-efficiency or standard-caller live-control gates.

This isolates current-main pipe progress and bounded raw diagnostic custody. It does not prove production provider behavior or task/recovery success.
