# #3266 stale-XID generation control — retained STOP

Decision: STOP_STALE_XID_REUSED

This is an additive container probe. It does not alter #3212, #3266, or prior construction evidence.

## H/T/D/C/U

- H: Fresh Xvfb display/profile/Chromium generations plus PID and X11 identity evidence can distinguish p1 from p2; an old XID must not resolve as a valid p2 identity.
- T: Debian bookworm-slim container; Chromium/Xvfb/Openbox/xdotool; p1 on display :151 with fresh profile/CDP port, terminate p1 and destroy display, p2 on :152 with fresh profile/CDP port; record process PID, WM_PID, XID and window name.
- D: Retain exact generation values and the stale-XID lookup result. PASS requires p1/p2 identity agreement, distinct generation identity, and stale-XID rejection before any input/effect.
- C: The positive identity subchecks are informative only. The allocation is STOP if an old XID is reused or resolves to p2.
- U: No keyboard/mouse input, no application effect, no CDP mutation, no formal p1/p2 action allocation, no production claim.

## Obstac result

Dependencies and Xvfb/Chromium/Openbox started successfully.

- p1: Chromium process 3410, XID 4194307, WM_PID 3410, title p1
- p2: Chromium process 3566, XID 4194307, WM_PID 3566, title p2
- stale lookup on p2 display: old XID 4194307 resolved to WM_PID 3566
- result: OBSTAC_DISPLAY_GENERATION STOP_IDENTITY_GATE

The XID was reused across destroyed displays. PID/display/profile/CDP generation evidence is therefore mandatory; XID alone is not an authority. Because the stale-XID gate failed, no input or application-effect gate was attempted.

## Next successor gate

Keep the result immutable. Extend the experiment only with a preregistered stale-XID rejection rule that binds display generation, Chromium PID/start time, CDP browser/document target and X11 WM_PID before input. Add a positive p2 effect and negative old-process/old-target controls only after that admission gate is independently passing.
