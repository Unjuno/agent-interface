# Preregistration — Issue #7426 T0 method-only A01

**Question.** Can a set-valued linear route ranking separate hard eligibility, task-mix uncertainty, and value-weight uncertainty on a finite synthetic table, while revealing cases where a fixed aggregate hides ranking reversals?

**Scope.** Construction/method-only. No model, GUI, route execution, live task, or empirical route recommendation. No allocation/resource use. The checked object is a deterministic exact-rational enumerator over synthetic outcomes.

**Frozen method.** Lower outcome values are better. First exclude any route failing any declared hard gate. For eligible routes, for each task-mixture vector `p` and non-safety value vector `w`, score route `r` as `sum_s p[s] * sum_k w[k] * cost[r,s,k]`. Enumerate the Cartesian product of the declared finite rational-grid mix set and value-weight set. Report robust dominance only when the same route is strictly better for every enumerated `(p,w)` pair; report tie/incomparability where pairs disagree or tie. A missing outcome in a stratum with positive admissible mixture mass makes that comparison `HOLD_UNIDENTIFIED_OUTCOME`; do not impute it. A route failing a hard gate is excluded before scoring, regardless of cost.

**Frozen grid.** Rational simplex points with denominator 6 (all nonnegative integer triples summing to 6 divided by 6). The same full simplex grid is used for task mix and value weights in the general robust fixtures. Separate controlled reversal fixtures pin one dimension to a declared singleton: mix-reversal pins weights to `(1,0,0)`; value-reversal pins mix to `(1,0,0)`. This deliberately includes zero weights; any conclusion is conditional on that declared set.

**Fixtures.** Six: (1) A componentwise dominates B in all 3 strata × 3 outcomes; (2) deliberately crossed faster/costlier outcomes in two strata; (3) task-mix reversal at fixed latency-only value; (4) value-weight reversal at fixed stratum; (5) a missing cost cell in a stratum that can receive positive mix mass; (6) a low-cost route failing a hard safety/correctness gate. The exact values are embedded in `rank.py` and independently repeated in `audit.py`.

**Conventional comparator.** Equal task mixture and equal outcome weights (both `(1/3,1/3,1/3)`), with hard gates applied first. It is descriptive only, not a justified user utility.

**Mutations.** (a) Change one dominance-fixture cell to reverse componentwise dominance; (b) flip a task-reversal stratum's latency delta; (c) restrict the allowed value weights to the latency-only singleton; (d) change the low-cost route's safety gate from fail to pass; (e) add a missing outcome value. The decision must change, narrow, or remain HOLD in the predicted direction.

**Decision rule.** `METHOD_PASS_SCOPED` only if independent audit agrees on every rational-grid pair and fixture disposition; dominance and both reversal types are exposed; missingness refuses ranking; hard-gate failure cannot be compensated; all mutations change/refuse as predicted. Any disagreement or unsafe inclusion is `FAIL_METHOD`. This is not an empirical route result or product recommendation.
