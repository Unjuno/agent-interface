# Issue #3212 live v2 process-epoch audit — 2026-09-20

Additive live successor. Earlier v1 PASS/HOLD and PID-reuse gap records remain unchanged.

## H/T/D/C/U

- H: The v2 generation/start-order guard accepts real same-display Chromium recovery only when the new process start tick is strictly later than the old one and the independent DOM effect is present.
- T: Three fresh Docker `--network none` allocations with real Chromium/Xvfb on display `:155`, same numeric XID, Xlib/XTEST, CDP DOM oracle, and `/proc/<pid>/stat` process start ticks. Each allocation produced three audit controls: stale_xid, old_process, positive_p2_effect.
- D: Process transitions were `PID 10/start 3337347 → PID 131/start 3337650`, `10/3337857 → 132/3338135`, and `10/3338340 → 131/3338615`. P2 DOM effect passed 3/3. The v2 audit over 9 rows returned `PASS_AUDIT_V2 rows=9 controls=3 errors=0`; no X11 `BadMatch` occurred.
- C: `PASS_CHROMIUM_LIVE_V2_PROCESS_EPOCH_SCOPED`. This is live fixture evidence that the v2 guard accepts real new process epochs and rejects the separately retained same-generation adversarial control. It is not a universal browser/restart claim.
- U: Retain generated launch epoch, process identity, CDP target, X11 window, and raw manifest directly from the runner rather than assembling audit rows post hoc; repeat timeout/cancel and graceful restoration with the same v2 schema.

## Raw audit result

```text
PASS_AUDIT_V2 rows=9 controls=3 errors=0
```
