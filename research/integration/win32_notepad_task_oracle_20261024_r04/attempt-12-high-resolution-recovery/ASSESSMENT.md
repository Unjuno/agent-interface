# R12 — high-resolution retained recovery timing

## Outcome

**PASS_SCOPED_BOUNDED_RECOVERY.** The public in-process standard MCP server used the production supervised-Win32 owner, recovery helper, and independent state observer. The producer fault injection held after native `SendInput(SHIFT-down)` returned. Preflight bound the empty Notepad document and SHIFT-up to generation `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`. During the hold SHIFT-down was independently observed. The terminal dispatch and retained action/cancellation both reported recovered; release was confirmed, replay denied, producer exit code was `-15`, and a separate same-generation read observed SHIFT-up. Bounded document readback remained empty.

## Timing

- Owner request `perf_counter_ns`: 531939332036700
- Owner recovery/readback confirmation `perf_counter_ns`: 531939349276200
- High-resolution owner interval: 17239500 ns (17.2395 ms)
- Monotonic request/completion interval: 32000000 ns
- Monotonic cleanup deadline: 531942296000000
- Monotonic deadline margin: 2968000000 ns
- Independent arithmetic check: `True`

The high-resolution value is the owner-side interval from accepting the cancellation request to evaluating both the accepted release and matching neutral readback. It is not physical keyboard latency. The monotonic clock remains the deadline authority; the accepted terminal state confirms completion before that deadline. The 17.2395 ms high-resolution interval and 32 ms monotonic interval are distinct clock measurements, and the latter reflects the host's coarse tick.

## Limits

This is one recovery-only sample. It does not test a hang inside `SendInput`, arbitrary platform I/O, stdio transport, task success, MAP01, matched efficiency, or broad reliability. `task_success` is null. `interface_close.release_confirmed=false` is a separate teardown result; the action/cancellation receipts and independent key-up observation confirm the operation's recovery. No WSLc or Docker allocation was used.

## Evidence

`preflight.json`, `RESULT.json`, `run_measured_recovery.py`, per-call request/report JSON, raw observe/cancel/dispatch/results/close responses, and screenshot are preserved in this attempt directory. The parent packet SHA-256 manifest covers these artifacts.
