# Construction-only visibility and capture diagnostic

Parent issue: [#4466](https://github.com/Unjuno/agent-interface/issues/4466)

This is excluded construction, not the formal allocation. It uses no keyboard or
pointer input and makes no application-state change. Its only window-management
mutation is moving the render-only decoy away from the target using X11
`ConfigureWindow`.

## Question

Does `xwd -id <target>` return target RGB pixels when the same-size decoy is
stacked over it, and what do X11 `Map State`, root-tree stacking, active-window,
and focus records report? Compare that with repeated target-only captures and
captures after moving the decoy to a non-overlapping position.

## Fixed construction sequence

One private Xvfb display, one live GTK target, three consecutive target-only
captures at 250 ms intervals; launch a same-title/same-size render-only decoy,
then three captures of both windows with the decoy at its initial position;
move only the decoy to x=400 (target is 400 px wide), verify non-overlap, then
three more captures of both windows. Record XWD bytes, SHA-256, decoded RGB
header/masks, unique RGB colors, changed RGB pixel count and bounding box,
window identities, `xwininfo` map/geometry, root tree, active-window/focus,
monotonic timestamps, process exit and stderr. A distinct X11 session is not
reused. All output goes to a new host evidence directory.

## Construction gate for formal preregistration

Proceed to a separately frozen formal calibration only if all 9 scheduled
capture groups are complete, both windows retain their expected PID/XID/title
and 400x180 geometry, decoy overlap and non-overlap are confirmed by geometry,
the target-only RGB repeatability is measured, and obscured-window capture
validity has a clear independent state signal. If the target image becomes
black while its X11 attributes still claim viewable, or RGB results cannot be
reconciled with map/stacking/focus, retain construction as HOLD and redesign the
capture-validity gate before formal allocation. Never treat an invalid/obscured
capture as a task effect.

## Environment and provenance

- Source snapshot: current main `c83ddb057c680a126144d000bf7ef7ba2274652a`.
- Docker image: `sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba` (linux/amd64).
- Runtime: `--pull=never --network none --read-only`; source mounted read-only; only `/tmp`, `/run`, and the fresh evidence directory writable.
- Model/provider calls: 0. GUI input: 0. Application effects: 0.

This construction result is descriptive. It cannot pass #3240 or #2606 and does
not estimate false-positive rates beyond this fixed fixture schedule.
