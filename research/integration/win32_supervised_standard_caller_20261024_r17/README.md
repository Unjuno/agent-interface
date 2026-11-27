# Win32 supervised standard MCP cancellation with a 2 s retained hook — R17

R17 is a one-shot local Windows trial through the public stdio-MCP caller,
frozen at source `9d0342e35aa2e0fd03f5c08f29b6c8bbf331fb47`. On Windows 11 Pro
build 26300, with `LowLevelHooksTimeout` not configured, it holds the first
injected Q-down callback for 2000 ms after public cancel (2400 ms self-release
cap). This crosses the documented 1000 ms maximum by a full second.

R17 corrects the R16 program's stale sentinel in the frozen operation list and
retains the post-receipt independent readback. The first readback is only a
baseline; a second same-generation sample starts after same-call
`recovered / release_confirmed=true`. A pass requires that sample to observe
Q-up before callback return, exact task effect, and complete cleanup. This
separates Q-up before the injected down reaches the fixture from Q-up after
recovery. No replay or rerun.

Only this user-authorized PC and one owned fixture are used. No WSLc or Docker
allocation is used. Runtime `task_success` remains unclaimed. R14, R15, and R16
remain preserved.
