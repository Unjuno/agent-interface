# Two ordinary relay requests ahead of guarded cancellation (2026-10-28)

## Condition

A local Fake JSON-lines input preloads 16 ordinary requests to fill `MAX_PENDING_STDOUT_RESPONSES`, then two additional ordinary requests, `interface_guarded_cancel`, and a tail request. The first stdout write blocks on an event. The Fake MCP client records calls and signals when cancellation reaches it. The test leaves stdout blocked for at least 100 ms after the relay has read the two queued ordinary requests, then releases stdout and waits for the cancellation call. No runtime or external input is generated.

## Result

While stdout remains blocked, the relay has read 18 lines (the 16 response-slot requests plus the two deferred ordinary requests) and has not dispatched either ordinary request or cancellation. After stdout resumes, calls are ordered: the 16 initial ordinary requests, queued ordinary #1, guarded cancellation, queued ordinary #2, then the tail. This confirms the relay's one-line priority lookahead: cancellation does not bypass two queued ordinary requests while output is fully blocked, and one ordinary MCP call is dispatched before the cancellation after output resumes.

The test is in `runtime/cli_v1/test_mcp_relay.py`. The full relay module passes 23/23 in normal and optimized Python (`-O`) on Windows CPython 3.11.9. Focused and full-suite logs/exit codes are retained. `attempt-01-import-error-transcription.txt` is a labeled transcription of a harness import failure; `attempt-02-wrong-order-assertion.*` preserves the first observed order that corrected the assertion.

## Scope

This is relay admission-order evidence using Fake streams and a Fake MCP client. It does not establish that the queued tool produced physical input, that cancellation released any key/button, or that an application task succeeded. It measures no hard safety deadline and does not qualify native GUI, WSLc, Docker, or MAP01 behavior. The confirmed delay remains an open control-plane boundary.

`SHA256SUMS` covers all packet files except itself, plus the modified source and design note.
