# Issue #3212 matched reuse versus fresh control — 2026-09-20

Additive within-allocation comparison. All earlier records remain unchanged.

## H/T/D/C/U

- H: Holding a validated Chromium session/resource receipt can avoid a fresh browser launch/readiness cost while preserving the same independently observed effect and fail-closed receipt cases.
- T: Three Docker `--network none` allocations of `mixed-formal-2992-debian:20260920`, Xvfb, Xlib/XTEST, CDP DOM oracle. In each allocation: p1 ready-gated action, same-session fixture reset and reuse action, then p2 fresh-profile launch and identical action. The receipt policy and DOM postcondition were unchanged.
- D: Reuse input→DOM: `821.360 / 811.810 / 818.982 ms`. Fresh-control input→DOM: `826.123 / 816.149 / 820.764 ms`. Fresh-control launch→ready: `412.347 / 394.459 / 470.942 ms`; fresh-control total launch→DOM: `1238.471 / 1210.610 / 1291.707 ms`. DOM effects passed for reuse and fresh control in all three allocations; session/resource/duplicate receipt cases were denied; no `BadMatch` occurred.
- C: `PASS_CHROMIUM_REUSE_EFFECT_AND_GUARD_SCOPED`; `BENEFIT_LAUNCH_READY_AVOIDED_SCOPED`. Reuse did not materially reduce input→DOM effect time (`-4.763, -4.339, -1.782 ms` versus fresh control), but avoided the measured fresh launch→ready cost of `394.459–470.942 ms` for the second action. This is not a model-wait, reacquisition, production-latency, or universal browser claim.
- U: Add a true `FRESH_ONLY` arm with the same number of actions and charge all model-wait/reacquisition/cleanup costs; repeat over timeout/cancel/restart and changed-source cases before claiming reusable receipt benefit.

## Raw summary

```json
{"runs":3,"reuse_input_to_dom_ms":[821.360,811.810,818.982],"fresh_input_to_dom_ms":[826.123,816.149,820.764],"fresh_launch_to_ready_ms":[412.347,394.459,470.942],"reuse_dom_effect":"3/3","fresh_dom_effect":"3/3","negative_cases_denied":"3/3","badmatch_runs":0,"formal_decision":"PASS_CHROMIUM_REUSE_EFFECT_AND_GUARD_SCOPED","benefit":"BENEFIT_LAUNCH_READY_AVOIDED_SCOPED"}
```
