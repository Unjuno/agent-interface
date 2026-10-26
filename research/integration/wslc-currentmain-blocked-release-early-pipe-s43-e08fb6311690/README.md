# WSLc S43 early-poll recovery trial

One preregistered WSLc 3.0.3 private-Xvfb run exercised the standard MCP caller after a test shim made the first two supervisor result-pipe polls return early. The third poll received the real cancellation response. The retained raw-data audit passes 28/28.

The owner release readback occurred 3,943.861 ms after cancellation admission, the independent all-up readback at 3,998.095 ms, and the delayed-event horizon at 8,504.358 ms. Both synthetic task oracles passed. The canceled public call correctly remains UNKNOWN, replay-denied, and `task_success=null`.

See [RESULT.md](RESULT.md), [conditions](conditions/CONDITIONS.json), [raw result](raw/output/result.json), [poll trace](raw/output/early-poll-trace.json), and [audit](AUDIT.json).

The trial used source commit `c058acb`; the four frozen runtime/test Git blobs are byte-identical to current main `949fd12`. This is synthetic Xvfb evidence with an injected pipe-poll fault. It does not establish native Windows kernel-pipe timing, physical GUI/MAP01 behavior, a latency guarantee, reliability, or efficiency. The [custody assessment](CUSTODY-ASSESSMENT.md) records limitations in the host invocation and dependency manifests.
