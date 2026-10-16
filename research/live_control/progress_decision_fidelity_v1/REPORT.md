# Extrema-preserving progress decision fidelity

Decision: **PASS_EXTREMA_PRESERVING_PROGRESS_DECISION_SCOPED**.

Issue #716. Immutable publication BASE `8b3527e7d95b1b08018a52260951537bf8527485`. Additive scope only under `research/live_control/progress_decision_fidelity_v1/**`.

## Question

With barrier-aware progress-run segmentation fixed, does a summary that keeps only the latest confidence preserve a frozen downstream rule `confidence < 0.70 => NEEDS_DECISION`, or is the run minimum required?

## Container-first method

- `py_compile`: PASS
- deterministic construction tests: **9/9 PASS**
- formal runner: **1 invocation**
- formal reruns: **0**
- verifier: **PASS_VERIFY**
- post-result source hash recheck: **7/7 exact**

Frozen threshold/operator: `0.70`, strict `<`.

## First outcome

Across **9** frozen progress segments:

- latest-only summary missed raw `NEEDS_DECISION` **3** times;
- extrema summary (`worst_confidence=min(run)`) disagreed with raw decision **0** times.

Concrete negative control: `[0.91, 0.64, 0.93]` yields raw `NEEDS_DECISION`, latest-only `CONTINUE`, extrema `NEEDS_DECISION`. Equality control `[0.91, 0.70, 0.92]` remains `CONTINUE` under the frozen strict `<` rule.

Critical-barrier case preserves exact `TARGET_LOST` identity/order and evaluates the pre/post progress runs separately. Cross-session decisions remain scoped (`A=NEEDS_DECISION`, `B=CONTINUE`).

All **8/8** frozen gates are true.

## Interpretation

A latest-value-only coalesced progress representation is insufficient for a monotone "did confidence ever fall below threshold?" decision: later recovery erases the transient dip. Keeping the bounded run minimum is sufficient for the exact frozen threshold rule while preserving the coalescing boundary established by #712.

This is representational decision fidelity only. It does **not** validate the numerical threshold, confidence calibration, model/planner behavior, token savings, interrupt savings, real watcher classification, latency, or production scheduling.
