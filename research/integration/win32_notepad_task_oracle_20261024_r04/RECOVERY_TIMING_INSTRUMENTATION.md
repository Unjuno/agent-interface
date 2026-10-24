# Recovery cleanup latency instrumentation

## Change

At the Win32 custody owner, an accepted cancellation now records `cleanup_requested_monotonic_ns`. When recovery release and independent neutral readback are both accepted before the cleanup deadline, the retained result also records `recovery_completed_monotonic_ns` and `cleanup_latency_ns` (their difference). Late or unconfirmed recovery leaves completion and latency null. Repeated cancellation does not reset the original request timestamp.

The completion timestamp is taken when the owner evaluates the release/readback receipt, after both helper receipts have returned. It measures the full recovery-and-readback confirmation path against the owner monotonic clock, not physical keyboard interrupt latency. The owner still enforces strict `< cleanup_deadline_ns` before setting `recovered`.

## Evidence and source state

- Base commit: `16dfc8843564d3768a767aaa85b165fd3c8c0cd3` (`origin/main` before this change).
- Files changed: `runtime/guarded_win32_v1/operation_owner.py`, `runtime/guarded_win32_v1/test_operation_owner.py`, and `runtime/cli_v1/test_mcp_supervised_win32.py`.
- Red-green proof: new owner latency test failed first because `cleanup_requested_monotonic_ns` was absent; it passed after implementation.
- Standard caller composition test verifies both timestamps and latency are present in `interface_results` and recovery completion is before the deadline.
- Local tests: `runtime.guarded_win32_v1.test_operation_owner` — 16 passed; `runtime.guarded_win32_v1.test_process_cancellation` — 12 passed; `runtime.cli_v1.test_mcp_supervised_win32` plus `runtime.cli_v1.test_mcp_win32_composition` — 29 passed; composed timestamp test rerun separately — passed.
- Combined test runs had one-second async/helper startup timeouts on two separate attempts; each affected test passed on isolated rerun and all modules passed when run separately. Keep these scheduling-sensitive tests under observation.

This prepares future native runs to report measured recovery latency from the retained receipt. It does not retrofit timestamps into historical R10 raw records and is not a new live experiment or proof of model efficiency.

## High-resolution follow-up

R11 showed that this host's `monotonic_ns()` resolution is 15.625 ms. The owner now also records `cleanup_requested_perf_counter_ns`, `recovery_completed_perf_counter_ns`, and `cleanup_latency_perf_counter_ns` from `time.perf_counter_ns()`. The original monotonic request/completion values and strict monotonic deadline gate remain unchanged. The high-resolution interval is populated only for confirmed recovery; unconfirmed/late outcomes keep completion and latency null. It measures owner-side receipt processing, not physical key-up latency. The retained R11 record predates this field and is intentionally unchanged; a subsequent run must capture the new interval before it can support a live duration claim.

The deterministic owner test uses independent fake monotonic and performance clocks. A standard caller test verifies that the high-resolution fields survive in `interface_results`. Local verification after this extension: owner tests 17 passed; process-cancellation tests 12 passed; standard supervised-Win32 and composition tests 29 passed; optimized owner tests plus the composed retained-result test 18 passed.
