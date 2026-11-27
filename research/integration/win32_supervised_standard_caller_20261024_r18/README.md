# Win32 supervised standard MCP producer liveness during blocked hook — R18

R18 is a one-shot local Windows attempt through the public stdio-MCP caller,
frozen at source `9d0342e35aa2e0fd03f5c08f29b6c8bbf331fb47`. It repeats the
2000ms callback hold with the corrected R17 sentinel, while adding exact
producer liveness samples using PID plus process creation time and a separate
Win32 process handle. Same-call status, release receipt, hook state, independent
Q-state, exact effect, and cleanup remain recorded.

The question is whether the producer process remains alive throughout the
blocked interval after public cancel, and whether its exit follows callback
release. The audit requires at least four exact-identity liveness samples during
the hold. This is one new measurement attempt, not a rerun of R17. No replay or
rerun. Only the user-authorized PC and one owned fixture are used; no WSLc or
Docker allocation is used. Runtime `task_success` remains unclaimed.
