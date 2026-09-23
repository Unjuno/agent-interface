# Issue #3212 display-aware recheck — 2026-09-20

Independent fresh-allocation recheck of the display-aware result. Earlier records remain unchanged.

## H/T/D/C/U

- H: The display-aware receipt identity and cross-display fail-closed guard remain reproducible in a fresh Docker allocation.
- T: One fresh `mixed-formal-2992-debian:20260920` Docker run with `--network none`, p1 on Xvfb `:155`, p2 on new Xvfb `:156`, Xlib/XTEST input, and read-only CDP DOM oracle.
- D: Runner decision `PASS_CHROMIUM_LIVE_RECEIPT_SCOPED`; `display1=:155`, `display2=:156`, `xid1=xid2=4194307`; valid DOM effect `saved=true,value=abc`; fresh-control DOM effect also passed; cross-display transplant admission was false with reset DOM; source-lineage, browser-exit, timeout, cancel, session, resource, and duplicate rows were denied. No stderr or X11 `BadMatch` occurred.
- C: `PASS_CHROMIUM_DISPLAY_AWARE_RECHECK_SCOPED`. This independently confirms the prior display-aware live evidence; it remains scoped to the fixture and does not implement the production schema.
- U: The remaining work is implementation integration and same-display new-generation recovery, not another claim that numeric XID alone is sufficient.

## Raw result excerpt

```json
{"decision":"PASS_CHROMIUM_LIVE_RECEIPT_SCOPED","display1":":155","display2":":156","xid1":"4194307","xid2":"4194307","valid_dom":"saved=true,value=abc","cross_display_admitted":false,"cross_display_dom":"saved=,value=","badmatch":false}
```
