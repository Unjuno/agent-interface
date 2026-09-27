# Issue #3212 live display/generation audit — 2026-09-20

Additive execution record connecting the live Docker result to the independent audit contract. Earlier records remain unchanged.

## H/T/D/C/U

- H: The independent display/generation audit accepts a real positive p2 effect only when CDP browser PID, CDP target display/profile, Chromium PID, and X11 window PID correlate; stale-XID and old-process controls must remain no-dispatch.
- T: Fresh `mixed-formal-2992-debian:20260920` Docker allocation with `--network none`, p1 on `:155`, p2 on `:156`, real Chromium/Xvfb, Xlib/XTEST, and CDP DOM oracle. The main-branch `issue-3212-display-isolation-v1/audit.py` was run in a separate Docker invocation against a JSONL derived from the retained live row: controls `stale_xid`, `old_process`, `positive_p2_effect`.
- D: Independent audit output was `PASS_AUDIT rows=3 controls=3 errors=0`. Live p2 DOM effect was `saved=true,value=abc`; stale/old controls had `dispatch=false,dom_effect=false`; p2 display/profile/PID and X11 window PID correlated. No X11 `BadMatch` or stderr occurred.
- C: `PASS_CHROMIUM_LIVE_DISPLAY_GENERATION_AUDIT_SCOPED`. This is a real fixture-level audit PASS, not a universal browser or production claim.
- U: Preserve raw JSONL and source/image digest manifests in the eventual runner integration; repeat with same-display generation replacement once the X11 persistence blocker is repaired.

## Raw audit result

```text
PASS_AUDIT rows=3 controls=3 errors=0
```
