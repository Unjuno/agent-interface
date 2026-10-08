# Issue #3212 cross-display receipt transplant — 2026-09-20

Additive live experiment; earlier records remain unchanged.

## H/T/D/C/U

- H: A receipt issued on display `:155` must not be transferable to a new Chromium resource on display `:156`, even when the numeric XID is identical.
- T: Three Docker `--network none` allocations with real Chromium/Xvfb, Xlib/XTEST, and read-only CDP DOM oracle. P1 issued a valid receipt on `:155`; p2 ran on fresh display `:156` and had the same numeric XID. P2 was first made to pass with its new receipt, then reset before replaying the p1 receipt under a display-mismatch guard.
- D: All runs had `display1=:155`, `display2=:156`, `xid1=xid2=4194307`. The p1 and p2 valid effects passed 3/3. Cross-display transplant admission was `0/3`; dispatch/effect were `0/3`; p2 DOM remained `title=ReceiptFixture`, `saved=""`, `value=""` in 3/3. No `BadMatch` occurred.
- C: `PASS_CHROMIUM_CROSS_DISPLAY_TRANSPLANT_FAIL_CLOSED_SCOPED`. Numeric XID equality is insufficient; display identity prevented unsafe transplant.
- U: Integrate this display identity into the production receipt schema/auditor, then repeat with same-display process replacement and a persisted new generation.

## Raw summary

```json
{"runs":3,"display1":":155","display2":":156","xid1":"4194307","xid2":"4194307","valid_effect":"6/6","cross_display_admitted":"0/3","cross_display_dispatch":"0/3","cross_display_dom_unchanged":"3/3","badmatch_runs":0,"formal_decision":"PASS_CHROMIUM_CROSS_DISPLAY_TRANSPLANT_FAIL_CLOSED_SCOPED"}
```
