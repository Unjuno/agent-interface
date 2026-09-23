# Issue #3212 new-display recovery — 2026-09-20

Additive successor experiment. Earlier graceful-restart STOP records remain unchanged.

## H/T/D/C/U

- H: If a restart allocates a new X display, resource identity must include display identity in addition to XID; equal numeric XIDs on different displays must not be treated as the same resource.
- T: Three fresh Docker `--network none` allocations. P1 ran real Chromium/Xvfb on display `:155`; after p1 termination, a new Xvfb display `:156` was started and p2 ran with a new profile/port. Xlib/XTEST input and read-only CDP DOM oracle were used for both effects. Receipt binding included display, session, resource, and generation.
- D: All 3 runs returned `PASS_CHROMIUM_LIVE_RECEIPT_SCOPED`; p1 display `:155`, p2 display `:156`; numeric XIDs were both `4194307` in every run, but the display identities differed. Both p1 and p2 DOM effects returned `saved=true,value=abc` in 3/3. Source mismatch, process-exit, timeout/cancel, and duplicate/session/resource negative rows remained denied. No `BadMatch` occurred.
- C: `PASS_CHROMIUM_NEW_DISPLAY_RECOVERY_SCOPED`. The new-display recovery path produced a valid independent effect and demonstrates that XID alone is insufficient identity. This does not prove graceful same-display restart, state restoration, or production browser generality.
- U: Integrate a display/server identity into the real receipt schema and repeat with a same-display new process once the process/window lifecycle is repaired.

## Raw summary

```json
{"runs":3,"display1":":155","display2":":156","xid1":"4194307","xid2":"4194307","p1_dom_effect":"3/3","p2_dom_effect":"3/3","negative_cases_denied":"3/3","badmatch_runs":0,"formal_decision":"PASS_CHROMIUM_NEW_DISPLAY_RECOVERY_SCOPED"}
```
