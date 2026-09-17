# #1116 Rung1 result

Decision: **PASS_RUNG1_TEMPORAL_SPECULATION_GAP_SCOPED**

One source-frozen formal invocation; reruns/replacements/tuning0.

## Primary
- CURRENT_ONLY hit: 75.782%
- TEMPORAL_INFORMED hit: 87.853%
- gain: +12.071 percentage points
- CURRENT_ONLY planner resumption: 24.218%
- TEMPORAL_INFORMED planner resumption: 12.147%
- CURRENT_ONLY mean realized→verified-effect: 25.339 ms
- TEMPORAL_INFORMED mean: 13.208 ms
- mean improvement: 12.131 ms
- WAIT_THEN_PLAN mean: 101.500 ms

All 100,000 primary cases per arm produced independently correct effects. Wrong admissions and prepared-authority laundering were zero.

## Controls
20,000 forced-reversal,20,000 expiry and20,000 no-authority cases per arm:
- pre-fallback forced-reversal admissions0
- expired-branch admissions0
- no-authority admissions/effects0
- fallback effects correct for reversal/expiry controls

## Interpretation
The Rung0 branch-allocation gain composes into lower logical useful-effect latency under a fixed100 ms simulated planner gap. The measured temporal preparation is a trivial bounded velocity feature; this favors retaining the simpler feature rather than claiming need for a rich history/model stack.

## Scope
Logical-clock controlled simulation only. No real frontier latency, OS input, GUI, model, or live capture cost. A later live/planner-gap rung is required for an end-to-end speed claim.
