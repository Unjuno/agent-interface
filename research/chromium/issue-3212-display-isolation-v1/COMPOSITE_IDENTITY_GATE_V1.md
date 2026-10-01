# #3266 composite generation identity gate v1

Decision: PASS_COMPOSITE_IDENTITY_GATE_SCOPED

This is a bounded identity/admission experiment following the immutable STOP in STALE_XID_REUSE_STOP.md. It does not claim input or application effect.

## H/T/D/C/U

- H: A candidate X11/Chromium target is safe to admit only when display generation, Chromium PID, CDP browser websocket identity, and WM_PID agree with the current p2 generation; an old p1 record must be rejected even when its XID is reused.
- T: Fresh Debian bookworm-slim container with Chromium, Xvfb and Openbox. Start p1 on :161 with profile p1 and CDP 9271; terminate and destroy it. Start p2 on :162 with profile p2 and CDP 9272. Record XID, WM_PID, process PID, display and CDP browser websocket. Evaluate an old-p1 candidate and a current-p2 candidate with the same admission predicate.
- D: Retain both positive and negative admission decisions, including the reused XID. No input is sent before admission.
- C: Scoped PASS requires old_admit=0, new_admit=1, and p2 WM_PID/process agreement.
- U: No keyboard/mouse input, no application mutation/effect, no stale-process liveness test beyond the terminated p1, no formal p1/p2 task allocation, no production integration.

## Obstac result

OBSTAC_COMPOSITE_IDENTITY_GATE PASS

- p1: display=:161, Chromium PID=3410, XID=4194307, WM_PID=3410
- p2: display=:162, Chromium PID=3561, XID=4194307, WM_PID=3561
- old XID lookup on p2: WM_PID=3561 (demonstrates XID reuse)
- old_admit=0
- new_admit=1

The same XID was reused, but the old record was rejected because display/PID/CDP generation did not match. The current p2 record was admitted only after the composite identity checks.

## Next gate

Add a positive p2 application-effect control and an old-CDP-target/old-process negative control. Preserve the composite predicate unchanged and retain all identity receipts before any input. This PASS does not close #3266 or establish GUI reliability.
