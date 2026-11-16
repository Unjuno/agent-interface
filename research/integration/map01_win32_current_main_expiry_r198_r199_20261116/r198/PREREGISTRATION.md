# R198 preregistration — 2026-11-16

- Attempt: `map01-native-expiry-delayed-input-r198-20261116`
- Source: current main `86a52662dc2bb690dd670d52ea8d97816aef2a26`; tree `c35b16d1df4f2e7c6b70a09e2ec672043ace5335`; runtime files: 1 1 1 1 1 1 1 1 1 1 1
- Conditions SHA-256: `6BE7E6D8AEDD045B6B6EB01C0BDB042861274A38E6D98A02165B800DC9031EBC`
- Scope: one fresh, non-replay native Windows MAP01 attempt. Existing executable and pinned game assets only. No external model/provider calls; this does not estimate integrated efficiency.
- Fault: one accepted LEFTDOWN, bounded 120 ms dwell, LEFTUP, then SHIFT held across a 3 s lease expiry while delayed SHIFTUP and second click are scheduled at 8 s; producer exits abnormally without backend cleanup.
- Required evidence: one dispatch and at most one recovery; delayed operations excluded; separate native LEFT button-up attempt and release confirmation; recovery at or below frozen deadline; integrated 2 s late-input horizon and independent 2 s neutral horizon; baseline HUD 50 and final HUD 49, both pistol-gated; normal bounded process close; custody clear afterward.
- Result limits: source action is UNKNOWN and `task_success=null` regardless of observed HUD change; no replay. Any gate, geometry, focus, recovery, release, horizon, custody, or effect mismatch is failure/unknown and is preserved as the sole attempt.
- Computer Use gate: passive screenshot of the unique returned GZDoom target window with MAP01 HUD visible; activate that selected window; record the returned screenshot ID, foreground HWND/root HWND, window ID and process ID in the attempt-bound receipt; independent runner validates foreground and ownership before any program input.
- Stop rules: if read-only preflight fails, no launch/input. If target selection or HUD visibility cannot be verified, no input. If attempt reaches uncertain state, preserve first result and do not replay.
