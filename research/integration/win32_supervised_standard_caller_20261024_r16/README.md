# Win32 supervised standard MCP cancellation beyond low-level-hook timeout — R16

R16 is a one-shot local Windows trial through the public stdio-MCP caller,
frozen at source `9d0342e35aa2e0fd03f5c08f29b6c8bbf331fb47`. It retains the
probe-owned low-level keyboard callback for 1250 ms after public cancel, beyond
the documented 1000 ms maximum timeout on Windows 10 version 1709 and later.
The current-user `LowLevelHooksTimeout` setting was read without change and was
not configured.

Unlike the R15 prelaunch-only packet, R16 can execute on this clean committed
source. It takes an initial independent sample, then starts a second independent
same-generation Q-state sample only after same-call cancellation reports
`recovered / release_confirmed=true`. The audit checks that this readback starts
after the receipt and finishes before the 1250 ms callback hold ends. The probe
also records whether `UnhookWindowsHookEx` finds a timed-out hook already removed.

A pass requires full callback hold, exact producer retirement, release receipt,
post-recovery independent Q-up before callback return, exact saved task effect,
and finite cleanup. No replay or rerun. Only the user-authorized PC and one
owned fixture are used; no WSLc or Docker allocation is used. Runtime
`task_success` remains unclaimed; R14 and the R15 prelaunch refusal remain
immutable.
