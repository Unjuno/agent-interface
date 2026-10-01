# Issue #57 — decision-scope T0 report

## Result

**METHOD_PASS_SCOPED**, as a pure local construction check. The source-pinned
snapshot at commit 0707d2254b2789c0bbab97d65645772c8da76a9f reproduces the
plan/frozen-HOLD wording mismatch while retaining the historical report's
RETAIN unchanged. The prospective table reconstructs all five cases:

| Case | Finite-allocation disposition | Claim scope |
|---|---|---|
| All finite gates pass; one sequence per arm | RETAIN | FINITE_SCHEDULE_ONLY |
| Accounting incomplete | HOLD | NO_POSITIVE_CLAIM |
| Formal integration discovery invalidates the allocation | HOLD | NO_POSITIVE_CLAIM |
| Verified correctness failure | REJECT | NO_POSITIVE_CLAIM |
| Frozen route threshold fails | REJECT | NO_POSITIVE_CLAIM |

Generalization is HOLD_NOT_ESTABLISHED for every case because no separate
generalization protocol is frozen. Thus the old finite-schedule RETAIN and a
hold on broader claims coexist without retroactively changing the prior report.
The eight mutation controls reject historical relabeling, generalized-claim
promotion, ignored accounting/discovery/correctness/threshold failures,
source-hash rebinding and hiding the plan/frozen-rule mismatch.

Local Python 3.12 construction suite: 13/13 pass. The test-first RED runs
observed the intended missing-evaluator and missing-auditor-summary failures
before their implementations. Candidate and independent auditor were both
executed locally; the compact output is retained in
`results/local-construction-01/RESULT.json`.

## Scope and execution

This is a pure local deterministic decision-table check. It used no Docker,
model, GUI, live allocation or new integrated route. Docker Desktop's local
daemon endpoint remained unresponsive in this task segment, so no container
run is claimed. The exact source commit and SHA256 pins are in fixture.json.

The prospective clarification is additive at
research/live_control/INTEGRATED_EFFICIENCY_DECISION_SCOPE_V2.md; the v1
plan now links it, while the historical preregistration and report bytes remain
unchanged.

## Limits and next gate

The test establishes only consistency of this finite decision table. It does
not establish statistical generalization, meaningful-gain uncertainty,
live-pair reset/order integrity or route efficiency. Before any future
integrated allocation, freeze the generalization population and inference
method separately, preserve all assigned pairs and attempts per the paired
ledger refinement, resolve remaining runtime integration gates, and run the
declared end-to-end workflow. Issue #57 remains open.
