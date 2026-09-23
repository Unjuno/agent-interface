# Issue #3212 ready-gated Chromium batch — 2026-09-20

This is an additive successor to the prior 1/3 DOM-effect batch. Earlier FAIL/HOLD/PASS records remain unchanged.

## H/T/D/C/U

- H: Waiting for both a mapped Chromium window and `document.readyState == complete` before XTEST input removes the startup race and makes the DOM effect reproducible.
- T: Three fresh Docker allocations using image `mixed-formal-2992-debian:20260920` (`sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`), `--network none`, Xvfb `:155`, isolated profiles, Xlib/XTEST input, read-only CDP DOM oracle. Only the launch wait condition changed; the receipt policy and negative cases were unchanged.
- D: 3/3 runner decisions were `PASS_CHROMIUM_LIVE_RECEIPT_SCOPED`; 3/3 DOM oracles returned `title=saved:abc`, `saved=true`, `value=abc`; 3/3 used distinct replacement XIDs (`4194307` and `12582915`); session restart, resource replacement, and duplicate receipt were denied in all 3; X11 `BadMatch` occurred 0/3. `model_calls=0`, `network_calls=0`.
- C: `PASS_CHROMIUM_LIVE_RECEIPT_SCOPED` for the frozen fixture, ready-gated input, and declared lifecycle cases. The earlier batch failure is retained as evidence that the ready gate is material. No reuse-latency benefit or production/general-browser claim is made.
- U: Compare reusable-plus-fresh-gate against `FRESH_ONLY` with measured wait/reacquisition latency, and extend the same independent postcondition discipline to timeout/cancel/orchestrator-restart cases.

## Raw batch summary

```json
{"runs":3,"runner_pass":3,"dom_effect_pass":3,"distinct_xids":3,"negative_cases_denied":"3/3","badmatch_runs":0,"model_calls":0,"network_calls":0,"formal_decision":"PASS_CHROMIUM_LIVE_RECEIPT_SCOPED"}
```
