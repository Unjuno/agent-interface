# Issue #4588 — confidence-trajectory information/noise construction rung

Allocation: `issue-4588-trajectory-20260927-01`. This is the first model-free, authority-neutral construction experiment for the open Issue, not a classifier, live-control or runtime-promotion experiment.

## H — hypothesis

Temporal confidence may resolve cases aliased under current level alone, and acceleration may resolve cases still aliased under level plus velocity. The second difference should amplify bounded measurement noise more than first difference; a frozen causal smoother may reduce that noise, with possible signal lag left for later testing.

## T — frozen experiment

- Corpus: 35 authored three-sample traces across 17 named transition families. The base corpus includes monotonic convergence/divergence, decelerating reversal, low-confidence acceleration, plateau, overshoot, oscillation, transient spike, stale history, epoch change, missing history, irregular intervals, self-correction, uncertainty and action-required state.
- Four current-level alias groups: same current confidence, three different typed labels (`ACTION`, `YIELD`, `NO_OP`).
- Four second-order alias pairs: equal current confidence and equal first difference, different label; the acceleration feature is checked for separation.
- Arms are represented without fitting: `CURRENT_ONLY`, `LEVEL_PLUS_VELOCITY`, `LEVEL_PLUS_VELOCITY_PLUS_ACCEL`, `SMOOTHED_TRAJECTORY`.
- Velocity and acceleration divide by observed intervals. Causal smoothing is frozen as `q0=p0; q1=(p0+p1)/2; q2=(p0+p1+p2)/3` before differentiating. No future sample is used.
- Noise stress is an exhaustive `{-0.01,0,+0.01}^3` grid (27 triples) around a constant signal; calculate RMS error for first difference, raw second difference, and causal-smoothed second difference.
- One invocation in OrbStack Docker, Python 3.12.14, Linux/amd64, network disabled, source read-only. No model, GUI, input or user data.

## D — decision

`PASS_CONSTRUCTION_INFORMATION_AND_NOISE_BOUNDARY` only when all 15 required base families and both alias families are present; all four current-level groups and second-order pairs are exact; invalid/stale/missing/epoch-mismatched history maps to `YIELD`; `NO_OP` and `YIELD` remain distinct; raw acceleration noise RMS exceeds velocity noise RMS; causal-smoothed acceleration noise RMS is lower than raw; independent raw audit passes. Any mismatch is preserved as FAIL/STOP/HOLD. This disposition only decides whether a larger held-out policy experiment is justified.

## C — controls

Every label and signal is authored; this is a synthetic identifiability/noise probe, not a natural-data estimate. There is no fitted model, so train/validation/test claims do not apply. The smoothing rule is causal and fixed before execution. No confidence value can grant execution authority; invalid history emits only `YIELD` in this contract fixture.

## U — limits

No claim about calibrated model confidence, realistic transition frequency, policy accuracy, false-action rate in deployment, user task success, learned-head capacity, optimal smoothing, latency/cost, cross-app transfer, or safe actuation. A PASS is only a rationale to freeze a held-out authority-neutral policy comparison next.
