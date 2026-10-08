# #1651 Temporal sample-count cost identifiability and break-even frontier

Decision: **PASS_TEMPORAL_SAMPLE_COST_NOT_IDENTIFIABLE_FROM_COUNT_SCOPED**

## What is proved

The retained temporal relation results say a universal fixed policy needs 11 source samples while a request-conditioned policy needs at most 4 for the frozen relation family. That count difference alone does **not** identify provider/model cost.

At identical `(11,4)` sample counts, three admissible nonnegative cost constructions exist:

- query cheaper: `F=11, Q=4, H=1` -> `H+Q=5 < F`;
- fixed cheaper: `F=2, Q=4, H=1` -> `H+Q=5 > F`;
- tie: `F=5, Q=4, H=1` -> `H+Q=F`.

Here `F` is the measured incremental cost of the actual fixed presentation, `Q` the measured incremental cost of the actual query-return presentation, and `H` the additional continuation/tool-boundary cost not already included in `Q`. Presentation identity is part of the measurement contract; source sample count is not a cost proxy when packing/layout/session/cache differ.

For any one commensurate metric, after cancelling common work:

`query cheaper <=> H + Q(k,p_q) < F(11,p_f)`.

The exact finite Fraction grid checked 4,913 `(F,Q,H)` points with candidate/direct mismatch 0.

## Linear special case

Only if both arms share the same presentation semantics and a constant per-sample marginal cost `c`, then:

`F=11c`, `Q=kc`, hence `query cheaper <=> H < (11-k)c`.

For worst-case `k=4`, the exact threshold is `H < 7c`. This special reduction is invalid if packing, segmentation, cache/session policy, or other provider processing differs.

The formal grid checked 4,160 `(k,c,H)` cases with mismatch 0.

## Multiple metrics

Wall time, tokens, and money are not silently additive. Without an explicit utility function there is no scalar overall winner. Queryable Pareto-dominates only when it is non-worse componentwise and strictly better in at least one declared metric; the symmetric rule applies to fixed. Otherwise the result is a tradeoff.

## Measurement consequence

A valid fresh temporal comparison must retain, per metric:

1. `F_m`: incremental cost of the exact 11-sample fixed presentation actually shown to the model;
2. `Q_m`: incremental cost of the exact selected query-return presentation;
3. `H_m`: extra continuation/tool boundary overhead, with no double counting;
4. presentation/session/cache identity for both arms;
5. correctness/model-value endpoint separately from cost.

Only these measured endpoints can establish a real break-even. Sample-count savings alone cannot establish token, wall-time, or monetary savings.

Scope: analytical measurement contract only; no actual provider/model/task/GUI/product cost claim.
