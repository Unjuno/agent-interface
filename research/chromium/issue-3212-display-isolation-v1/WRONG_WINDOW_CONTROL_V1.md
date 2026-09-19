# #3266 wrong-window input control v1

Decision: PASS_WRONG_WINDOW_CONTROL_SCOPED

## H/T/D/C/U

- H: An OS key sent to a decoy Chromium window must not mutate the admitted p2 application target.
- T: Fresh Debian bookworm-slim container; Xvfb :270 and Openbox; two fresh Chromium profiles on one display: p2 at CDP 9382 and decoy at CDP 9383. Install distinct key listeners through each current page target, activate only the decoy X11 window, send x with xdotool, and read both titles independently through CDP.
- D: Retain exact window selection, input command, and both post-input receipts. The p2 target must remain unchanged while the decoy changes.
- C: PASS requires p2_title=p2-ready and decoy_title=os-input-decoy.
- U: This is a wrong-window control only; no p1 teardown in this allocation, no old-process control, no cross-application reliability, no production integration.

## Obstac result

OBSTAC_WRONG_WINDOW_CONTROL PASS p2_title=p2-ready decoy_title=os-input-decoy

The input changed only the decoy window. The admitted p2 target did not change.

## Next gate

Combine this wrong-window control with the repeated p1→p2 stale-process/old-target controls and positive p2 input/effect under one frozen multi-window allocation. Preserve the composite identity predicate unchanged.
