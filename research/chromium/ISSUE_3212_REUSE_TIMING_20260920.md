# Issue #3212 same-session reuse timing — 2026-09-20

Additive timing experiment. Earlier PASS/FAIL/HOLD records remain unchanged.

## H/T/D/C/U

- H: Reusing a current session/resource receipt after a model-wait interval should reduce the action-to-independent-DOM-effect latency relative to the first fresh action, while preserving the same receipt guards.
- T: Three fresh Docker `--network none` allocations of `mixed-formal-2992-debian:20260920`, Xvfb, one Chromium profile per allocation, Xlib/XTEST input, and read-only CDP DOM oracle. Each allocation performed one ready-gated fresh action, reset the fixture through the DOM, then a same-session reuse action. This is a within-session comparison, not yet a matched fresh-relaunch control.
- D: Fresh input→DOM: `807.851 / 812.661 / 831.989 ms`. Same-session reuse input→DOM: `804.706 / 822.750 / 820.553 ms`. DOM effect was `saved=true,value=abc` for both actions in all three allocations. Launch→ready was `849.355 / 824.297 / 1014.977 ms`; no `BadMatch` was observed. Negative session/resource/duplicate receipt rows remained denied.
- C: `PASS_CHROMIUM_RECEIPT_REUSE_SAFETY_SCOPED`; `HOLD_REUSE_BENEFIT_UNMEASURED`. Safety/effect reproduced, but the observed reuse timing is not a clear benefit: differences were `-3.145, +10.089, -11.436 ms` (reuse minus fresh), with no controlled fresh-relaunch arm in this allocation.
- U: Run a preregistered matched arm with identical task schedule: `FRESH_ONLY` relaunch versus `REUSABLE_PLUS_FRESH_GATE`, charge launch/ready/model-wait/reacquisition costs, and retain independent DOM outcomes.

## Raw summary

```json
{"runs":3,"fresh_input_to_dom_ms":[807.851,812.661,831.989],"reuse_input_to_dom_ms":[804.706,822.750,820.553],"reuse_minus_fresh_ms":[-3.145,10.089,-11.436],"dom_effect":"6/6","negative_cases_denied":"3/3","formal_decision":"PASS_CHROMIUM_RECEIPT_REUSE_SAFETY_SCOPED","benefit":"HOLD_REUSE_BENEFIT_UNMEASURED"}
```
