# R13 — producer held at key-up send boundary

## Outcome

**PASS_SCOPED_BOUNDED_RECOVERY.** Preflight confirmed the blank Notepad document and SHIFT-up for generation `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`. The production supervised-Win32 producer sent SHIFT-down through native `SendInput`, then the fault hook blocked its next `_send` call for SHIFT-up before that call reached native `SendInput`. An independent state observation saw SHIFT-down while the producer was held. `interface_cancel` returned pending; the subsequent terminal dispatch and retained action/cancellation both reported recovered. The producer exited with code `-15`; the parent's recovery path reported release confirmed, denied replay, and a separate same-generation native read observed SHIFT-up. The document remained empty.

## Timing

- `perf_counter_ns` request: 532091840733900
- `perf_counter_ns` recovery/readback confirmation: 532091858279000
- High-resolution owner interval: 17545100 ns (17.5451 ms)
- Monotonic interval: 16000000 ns
- Cleanup deadline margin: 2984000000 ns
- High-resolution arithmetic check: `True`

The measured interval covers owner-side accepted cancellation through matching release and neutral readback confirmation. The monotonic clock remains the deadline authority. This is not physical keyboard latency.

## Limits

This tests a producer blocked at the backend call boundary before native key-up, after a real native key-down. It does not establish a hang inside `SendInput` or the OS kernel, arbitrary blocked-I/O bounds, stdio transport behavior, task success, MAP01 transfer, efficiency, or reliability. `task_success` is null. Close reports a separate `release_confirmed=false`; the terminal action/cancellation receipts plus independent SHIFT-up readback establish the operation's recovery. No WSLc or Docker allocation was used.

## Evidence

`RESULT.json`, `preflight.json`, the harness, raw observe/cancel/dispatch/results/close replies, per-call requests/reports, and screenshots are retained here and included in the packet checksum manifest.
