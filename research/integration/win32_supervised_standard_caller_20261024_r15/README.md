# Win32 supervised standard MCP cancellation beyond low-level-hook timeout — R15

R15 is a one-shot local Windows trial packet, frozen at source
`5de12e91bdf8d0d589f429a4f0d3eb422ef2111a`, for holding the probe-owned
low-level keyboard callback for 1250 ms after public cancel, beyond the
documented 1000 ms maximum timeout on Windows 10 version 1709 and later. The
current-user LowLevelHooksTimeout setting is recorded read-only and never
changed. Its preflight launch was refused before fixture creation because the
tracked worktree was dirty; no native input or public dispatch occurred. This
R15 attempt is preserved as a prelaunch failure and will not be rerun.

The unanswered scientific question is whether OS callback timeout lets the
exact producer retire, then permits one supervised recovery and same-generation
independent Q-up while the original callback remains blocked. The frozen pass
requires a full 1250 ms hold, same-call recovered/release-confirmed, independent
Q-up before callback return, exact task effect, and finite cleanup. Hook
unregistration status is captured to distinguish silent timeout removal.

Only the user-authorized PC and one owned fixture are used. No WSLc or Docker
allocation is used. Runtime `task_success` remains unclaimed; R14 remains
immutable. See `RESULT.md` for the prelaunch refusal.
