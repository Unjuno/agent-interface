# R16 — paired read-only physical-screen observation

## Question

For the same currently foreground Calculator HWND, does the public supervised-Win32 `screen_physical_px` route return visible Calculator pixels where R15’s correctly bounded `window_client` capture returned a uniform-black image?

## Frozen setup

Target HWND 55117672 / PID 35132; current UIA display must be 1043; target must be visible and the foreground root. The client is measured read-only immediately before freeze. Its current client rectangle maps to physical-screen region `[48, 32, 320, 533]`.

## Procedure

One public `interface_observe` with frame `screen_physical_px` and the frozen region; then one `interface_close`. No dispatch, input or task oracle. Preserve raw wrapper, image, generation, current geometry and close receipt. Stop before observation if UIA display, process/window identity, foreground root or geometry changes.

## Decision

Observation is visually useful only if one returned image matches the frozen dimensions, contains non-black pixels, and visibly shows Calculator’s 1,043 display. A returned status/target generation alone does not count. No conclusion about dispatch, release, recovery, efficiency or reliability follows.
