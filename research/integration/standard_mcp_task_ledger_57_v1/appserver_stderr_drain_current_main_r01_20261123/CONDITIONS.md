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

This isolates current-main pipe progress and bounded raw diagnostic custody. It does not prove production provider behavior or task/recovery success.
