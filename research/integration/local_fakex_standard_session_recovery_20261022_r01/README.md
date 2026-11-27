# Current-main Fake X fresh-session recovery check

**Result:** PASS, scoped, one focused unittest in both normal and optimized Python.
**Source:** `cdc8bd6b65bf976137db645c2be31e20090f7d67` (`origin/main` matched this SHA at run time).
**Host:** Windows host, CPython 3.11.9.
**Test source SHA-256:** `b6cd8774fec60390f0da41f2d050119cac13f5c6bc7bb80498066967dbb5810f`.

The test `runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_fresh_standard_session_recovers_after_prior_cancel_remains_unknown` passes in normal mode (3.485 s) and optimized mode (3.440 s). Terminal output records and the optimized exit code are in `raw/`.

The Fake X composition keeps the first session's cancellation `UNKNOWN`, `late_server_request_possible=true`, `release_confirmed=false`, `task_success=null`, and replay denied after cancellation and close fail closed. A new session has a distinct session ID, owner PID, and fake process generation; its one-transition compiled method receipt reports `TASK_SUCCEEDED`, and a test-side synthetic pixel receipt independently reports the expected red pixel. The old cancellation receipt remains value-identical after the fresh task. The fresh runtime action still has `task_success=null` and replay denied.

This confirms the local composed caller/fence behavior on synthetic owners. It does not exercise real X11 I/O, key-release readback, an 8 s server request delay, supervisor operation against Xvfb, physical desktop control, MAP01, WSLc portability, reliability, or matched efficiency. In particular, the Xvfb experiment in `../standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-01/` remains held before test invocation because the WSL2 shared X11 socket directory is read-only with mode 0777.

Commands:

- `python -m unittest -v runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_fresh_standard_session_recovers_after_prior_cancel_remains_unknown`
- `python -O -m unittest -v runtime.cli_v1.test_mcp_owned_process.OwnedProcessMCPTests.test_fresh_standard_session_recovers_after_prior_cancel_remains_unknown`
