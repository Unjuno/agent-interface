# V39 frame-only threat-change boundary A01

## H / T / D / C / U

- **H:** The current V39 paired health/ammo cover monitor does not revoke or refresh an active policy when a new observation has a different frame identity but unchanged typed health and ammo. This would leave a purely visual threat-onset cue outside the local guard while the planner is pending.
- **T:** At frozen current main, feed the production `DoomCoverSignalPairMonitor` one synthetic advancing typed observation with unchanged health/ammo, the same binding, and a changed frame RGB hash. Run the candidate once, then independently audit its raw result. No game, GUI, model, OS input, or X server.
- **D:** `CONFIRMED_BOUNDARY` only if the production monitor returns no invalidation, records no soft event, preserves the typed values, and advances sequence/frame identity. Any invalidation or value drift rejects this narrow hypothesis.
- **C:** The stimulus represents a frame-only visual change; it contains no real pixels, object labels, or classifier result. The test exercises the production guard API, not the full planner/Executor loop.
- **U:** This does not establish that a threat appeared in a live run, that image-only changes are unsafe, or that a visual detector would be reliable. It is not the required current-main live threat exposure and grants no allocation.

## Result

The one candidate run at main `53ec001a334e4077caf665ff56372cd4b0ccb068` returned no invalidation for an advancing observation whose synthetic frame identity changed while health stayed 61, ammo stayed 40, and binding stayed fixed. The monitor advanced to sequence 11, retained zero soft events, and granted no input authority. The independent raw audit passed 12/12 checks. Five mutation/audit regressions pass in normal and optimized Python.

This demonstrates only that a frame-hash change without typed HUD change is ignored by this local monitor. It does not test the frame pixels, classify threats, or establish whether the preserved policy is harmful. The candidate was run once; no retry or live allocation occurred.