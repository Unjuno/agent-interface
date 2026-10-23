# Win32 supervised standard MCP cancellation and recovery — R07

R07 repeats no prior attempt. It is a new one-shot live condition with a 45 second finite hook-entry window, chosen after R06 measured a 10.75 second gap between the zero-wait pending response and native Q-down. The dispatch returns its call ID first; after the hook confirms injected Q-down, the probe reads the same call and requires `action.status=running`, then issues one `interface_cancel`.

The action saves a unique R07 sentinel before Q-down. The packet measures the hook, exact producer exit by PID plus creation time, recovery Q-up, same-generation independent Q-state readback, fixture effect, and cleanup. The predeclared limits and audit require one dispatch and one cancellation, same-operation recovery, observed exit-before-UP, and neutral independent readback within 2500 ms. Runtime `task_success` remains null.

The prior R05 and R06 records remain immutable. Conditions, code, audit, preflight, and source hashes are frozen before this one trial. No WSLc or Docker allocation is used.
