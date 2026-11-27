# Win32 supervised standard MCP cancellation and recovery — R10

R10 is a one-shot local Windows trial through the public stdio-MCP caller. Its full frozen source commit is `1fe82f4907c699d27a31b4196557e969f965c5f0`. It extends the finite hook-entry window to 100 seconds and the lease to 180 seconds after R09's Q-down arrived 75.788 seconds after gate start and 78.482 seconds after hook readiness.

The one-run sequence is unchanged: zero-wait dispatch returns one call ID; the probe-owned low-level hook observes injected Q-down; the same call must still report `running`; then exactly one public cancel is issued. The hook releases immediately after the cancel response and has a 1.5-second self-release cap. Audit requires exact producer exit before recovery UP, same-generation independent all-up readback within 2500 ms, exact fixture effect, and complete cleanup. Missing the finite hook gate or any mismatch is retained as FAIL_OR_UNKNOWN; no retry or replay.

Only this user-authorized PC and one owned fixture are used. No WSLc or Docker allocation is used. The hook's harmless setup/teardown and Python compilation are preflighted before freezing the packet.