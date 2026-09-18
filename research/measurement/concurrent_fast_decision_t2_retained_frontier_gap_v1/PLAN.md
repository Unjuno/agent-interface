# #1451 retained requested-Astra frontier-gap eligibility

Base commit: `4f03b7a8ee80a2601a68ebd976d135f2db306ca4`
Issue: `Unjuno/agent-interface#1451`

## H/T/D/C/U freeze
Follow Issue #1451 exactly. No provider/model/network/GUI/X11/task-input/shared-runtime action.

## Frozen constants
- T1 useful-reaction deadline: 12 ms = 12,000,000 ns.
- Retained T1 max ACTIVATE useful-effect latency: 2.692318 ms = 2,692,318 ns.
- Expected requested model: `gpt-6-astra`.
- Expected requested effort: `medium`.
- Runs: `timing-envelope-openttd-l-02` through `-11`, `fixed-astra-control/model-1-stdout.txt` only.
- Git intake ref: `4f03b7a8ee80a2601a68ebd976d135f2db306ca4`.

## Statistical convention fixed before formal analysis
- All primitive durations are integer nanoseconds.
- min/max: exact order statistics.
- median: ordinary p50; for even n, exact arithmetic mean of the two center values.
- p95: linear interpolation on index `(n-1)*0.95` (Hyndman-Fan/R type 7 convention), retained as an exact rational number of ns.
- Ratios use exact rational division by 2,692,318 ns and are rendered to 9 decimal places only for reporting.

## Formal execution contract
- Source-first SHA-256 freeze before execution.
- Exactly one invocation of `analyze.py`.
- No rerun/replacement/tuning.
- Exactly one independent invocation of `audit.py` after the formal output exists.
- Auditor independently decodes raw bytes, verifies Git blob SHA-1, reparses JSON, recomputes all durations/statistics/ratios, and checks disposition.
