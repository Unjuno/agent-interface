# R02 — public MCP screen-capture path and Calculator effect

R01's single public `window_client` observation returned a uniform black image
for the visible Calculator HWND and correctly stopped before input. R02 changes
only the observation frame to `screen_physical_px`, which uses the desktop
capture branch. It is a new attempt with its own frozen source, raw capture,
and stopping rule; R01 is immutable.

The fixed task is `314 + 728 = 1042`. Before dispatch, inspect the one fresh
screen observation. Continue only if it visibly shows the configured Calculator
window in Standard mode with a display of `0` and the target remains the
foreground window. Then validate the single frozen click program once and
dispatch it once. After a terminal result, take one read-only public MCP
screen observation for visual effect evidence. Never retry or recover.

Stop before input on a black, occluded, unexpected, or mismatched observation,
generation mismatch, or failed validation. Stop after any uncertain dispatch or
release. Preserve UNKNOWN. `interface_close.release_confirmed` is not an action
release result. This is one task-effect trial; it makes no efficiency or
reliability claim, does not qualify blocked native I/O, and uses no WSLc or
Docker allocation.
