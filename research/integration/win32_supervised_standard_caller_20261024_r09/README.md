# Win32 supervised standard MCP cancellation and recovery — R09

R09 is a new one-shot local Windows trial through the public stdio MCP caller. Its conditions use the exact full source commit and a 75 second finite hook-entry window, longer than the 45.7678 second delay measured in R07. The one-use authority lease lasts 150 seconds so the pending dispatch can finish producer startup within that window.

The dispatch returns its call ID with zero response wait. After a probe-owned low-level hook confirms the injected Q-down, the runner reads the same call and requires `action.status=running`, then issues exactly one `interface_cancel`. The hook holds the Q-down for at most 1.5 seconds and is released as soon as cancel returns. The packet records exact producer identity/exit, recovery Q-up, same-generation independent Q-state readback, fixture task effect, and cleanup.

PASS requires recovered custody, producer exit before recovery UP, independent neutral readback within 2500 ms, exact effect, and full cleanup. Any failure is preserved without retry. Frozen conditions, runner, audit, preflight, and source hashes precede the only run. No WSLc or Docker allocation is used.
