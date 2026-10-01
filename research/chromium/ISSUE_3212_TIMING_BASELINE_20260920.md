# Issue #3212 timing baseline — 2026-09-20

Additive Docker measurement after the ready-gated 3/3 DOM PASS. Earlier records remain unchanged.

## H/T/D/C/U

- H: A reproducible ready-gated Chromium receipt path has measurable launch, readiness, input, and independent-effect timing that can serve as the baseline for a future `FRESH_ONLY` versus reusable comparison.
- T: Three fresh `mixed-formal-2992-debian:20260920` Docker allocations, `--network none`, Xvfb, isolated Chromium profiles, Xlib/XTEST, and read-only CDP DOM oracle. Same ready gate and receipt policy as the preceding PASS.
- D: Timing (milliseconds): run1 launch→ready `998.920`, ready→input `8.508`, input→DOM `806.187`, total `1813.616`; run2 `794.513`, `4.363`, `837.438`, `1636.314`; run3 `888.011`, `3.846`, `842.547`, `1734.404`. DOM effect and negative-case receipt denials passed in all three runs; no `BadMatch` was emitted.
- C: `PASS_CHROMIUM_LIVE_RECEIPT_TIMING_BASELINE_SCOPED`. This is a baseline only. No reuse benefit, latency reduction, or causal comparison is claimed because a matched `FRESH_ONLY` arm was not run in this allocation.
- U: Run the preregistered matched `FRESH_ONLY` and `REUSABLE_PLUS_FRESH_GATE` arms with identical task/effect oracle, including model-wait simulation and reacquisition counts.

## Raw timing summary

```json
{"runs":3,"launch_to_ready_ms":[998.920,794.513,888.011],"ready_to_input_ms":[8.508,4.363,3.846],"input_to_dom_ms":[806.187,837.438,842.547],"total_ms":[1813.616,1636.314,1734.404],"dom_effect_pass":"3/3","formal_decision":"PASS_CHROMIUM_LIVE_RECEIPT_TIMING_BASELINE_SCOPED"}
```
