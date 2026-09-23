# Issue #3212 repeated DOM audit — 2026-09-20

This additive batch audits the prior scoped PASS. It preserves all earlier records.

## H/T/D/C/U

- H: The Chromium receipt/effect result should reproduce across independent Docker allocations, with the independent DOM oracle agreeing with the runner's decision.
- T: Three fresh Docker `--network none` runs of `mixed-formal-2992-debian:20260920`, Xvfb `:155`, isolated Chromium profiles, Xlib/XTEST input, and read-only CDP DOM oracle.
- D: Runner self-decision was `PASS_CHROMIUM_LIVE_RECEIPT_SCOPED` in 3/3 runs. Independent DOM results were successful in only 1/3: run 1 `value=""`, `saved=""`; run 2 `value=""`, `saved=""`; run 3 `value="abc"`, `saved="true"`. All three runs had distinct replacement XIDs (`4194307` vs `12582915`) and denied session/resource/duplicate cases. Run 2 emitted X11 `BadMatch` for resource `4194307`.
- C: `FAIL_CHROMIUM_LIVE_RECEIPT` for the repeated allocation, with the narrower effect interpretation `HOLD_CHROMIUM_LIVE_EFFECT_UNMEASURED`. The runner's hash-based `effect=true` is not an acceptable authority; DOM agreement was 1/3.
- U: Fix synchronization/focus/input delivery and make the independent DOM postcondition the decision gate. Re-run a frozen batch only after the runner cannot report PASS when DOM says no effect.

## Raw batch summary

```json
{"runs":3,"runner_pass":3,"dom_effect_pass":1,"dom_effect_fail":2,"distinct_xids":3,"negative_cases_denied":"3/3","badmatch_runs":1,"formal_decision":"FAIL_CHROMIUM_LIVE_RECEIPT"}
```

The earlier single-allocation scoped PASS remains in the history, but this repeated audit prevents promoting it to a reproducible result.
