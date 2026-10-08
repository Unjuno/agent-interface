# Issue #3212 same-display new-generation recovery — 2026-09-20

Additive successor to the prior same-display STOP records. Earlier records remain unchanged.

## H/T/D/C/U

- H: Same-display restart can be admitted safely when the old receipt's resource generation is distinguished by a new correlated Chromium/window PID, even if the XID is numerically reused; unchanged PID/generation must not be admitted.
- T: Three fresh Docker `--network none` allocations with one Xvfb display `:155`. P1 was terminated, p2 was launched with a new profile/port on the same display, and Xlib/XTEST plus read-only CDP DOM oracle measured the new effect. The runner required display equality plus a changed correlated window PID before accepting the new generation.
- D: All runs used `display1=:155`, `display2=:155`, `xid1=xid2=4194307`; window PID transitions were `10→134`, `10→130`, `10→133`. The new p2 DOM effect passed 3/3. Old process/session/resource/source/duplicate/terminal rows were denied, and no `BadMatch` occurred.
- C: `PASS_CHROMIUM_SAME_DISPLAY_NEW_GENERATION_SCOPED`. Numeric XID reuse is safe only when correlated process/generation identity changes and the new target passes independent DOM effect verification. This is fixture-scoped and does not prove arbitrary browser restart/state restoration.
- U: Emit process start epoch and CDP target identity directly from the live runner, retain generated raw JSONL/manifests, and test PID reuse or ambiguous correlation as explicit fail-closed controls.

## Raw summary

```json
{"runs":3,"display":":155","xid1":"4194307","xid2":"4194307","pid_transitions":["10->134","10->130","10->133"],"new_generation_dom_effect":"3/3","negative_cases_denied":"3/3","badmatch_runs":0,"formal_decision":"PASS_CHROMIUM_SAME_DISPLAY_NEW_GENERATION_SCOPED"}
```
