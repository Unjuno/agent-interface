# Results: public MCP Fake X late-down baseline reproduction R03

The targeted `test_standard_owned_caller_keeps_unknown_after_fake_late_down`
passed once with Python 3.13 normally and once with `-O`, using source commit
`2f8f10ae9d`. In both runs, the public MCP path produced and the fake upstream
captured a 36-byte XTEST KeyPress request. The separate cleanup readback then
reported all keys/buttons up. After that, the test directly added keycode 2 to
its own state list and labeled the event order as modeled; it did not decode or
re-deliver the captured bytes.

The runtime receipt remained `cleanup_status=UNKNOWN`,
`release_confirmed=false`, `task_success=null`, replay denied, and
`late_server_request_possible=true`. The terminal result was `runtime_failed`.

This is retained as the exact baseline for R04's source-level change. It does
not show that an old X server connection delivered a request after client
retirement. No live X server, GUI, WSLc, Docker, network, provider/model, or OS
input was used. Raw receipts and outputs are in `raw/` and are bound by
`SHA256SUMS.json`.
