# App Server stderr drain current-main R01

## Frozen regression

- Main source revision: `07c0d7f72bf19d0dc2690bc01a114e0912b20f87`.
- Host: Windows 11, CPython 3.13.14.
- Target: `research.live_control.test_appserver_stderr_backpressure_current_main_r01.AppServerStderrBackpressureCurrentMainTest.test_large_invalid_stderr_does_not_block_rpc_and_keeps_bounded_raw_tail`.
- A real local child process writes 1 MiB of binary stderr, including non-UTF-8 bytes, before reading one JSON-RPC request and returning a response.
- Pass only if the response arrives within 2 seconds, close retires within 3 seconds, and the client reports the exact 1 MiB byte count, complete EOF, no read error, and the exact 65,536-byte raw tail.
- The fixture invokes no real App Server, provider, GUI, Docker, WSL/WSLc, or external allocation.
- RED phase must fail specifically because stderr backpressure prevents the RPC response. Preserve unexpected setup failures separately.

This isolates current-main pipe progress and bounded raw diagnostic custody. It does not prove production provider behavior or task/recovery success.
