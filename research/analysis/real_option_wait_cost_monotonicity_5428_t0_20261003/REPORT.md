# Issue #5428 T0 — real-option wait-cost monotonicity

## H — Hypothesis

For the frozen pairwise decision contract, increasing the cost of waiting must
never change a `COMMIT` decision to `WAIT`; increasing the cost of lost
flexibility must never change `WAIT` to `COMMIT`. Hard authority, freshness,
safety, and commit-window gates dominate valuation. Unpriceable cases fail
closed to `HOLD`.

## T — Test

The decision rule is

```text
V_now  = commit_value - lost_flexibility_cost
V_wait = future_gross_value - wait_cost
COMMIT iff V_now >= V_wait, after the hard gates pass
```

The finite 5×5×3×3 grid (225 numeric cases) and ten named corner controls were
enumerated. A frozen candidate produced raw rows; a separate auditor
independently regenerated expected inputs and decisions, checked all rows,
and tested the two monotonicity relations. Construction checks passed 7/7
before freeze. One candidate and one auditor invocation were made, with zero
retries. Exact commands, runtime boundary, exits, and output hashes are in
`FREEZE.json` and `RUN.json`; pre-freeze construction failures are preserved in
`CONSTRUCTION_LOG.md`.

## D — Result

`PASS_METHOD_SCOPED`: 235/235 rows independently reconstructed; zero audit
errors; zero wait-cost monotonicity violations; zero lost-flexibility
monotonicity violations. Decisions: 135 `COMMIT`, 95 `WAIT`, 5 `HOLD`.
Hard-gate and unpriceable controls held; tie, expired-wait, and unavailable
wait-route cases followed the frozen contract. Raw output and audit digests
are recorded in `RUN.json`.

## C — Interpretation

The result verifies internal consistency and the two expected monotonicities
of this explicitly assigned finite utility rule over the enumerated values.
The inequalities follow directly from subtracting nonnegative costs in the
frozen rule; exhaustive enumeration also checks implementation and edge-case
conformance. Numeric utility values are author-assigned, not calibrated from
users, agents, markets, or a live system.

## U — Limits

This is an exact finite contract check, not a learned or empirically
calibrated policy. It establishes no real-world optimality, reversibility,
latency, utility calibration, safety, GUI behavior, task performance, or
transfer to another implementation. No model, GPU, network, external action,
or container was needed; this result makes no container-runtime claim. The
previous Issue #5428 T1 preregistered-model gate failure and fixed-trace T2
result remain unchanged and are not pooled with or superseded by this fresh
T0 contract check.
