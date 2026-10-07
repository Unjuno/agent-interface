# Issue #5309 A12 — held-out effect semantics

This is a new, main-based allocation. It does not modify A04–A11 evidence or reinterpret A11's formal FAIL. The question is whether a raw-only scorer can distinguish model prediction correctness from realized, independently witnessed task effect on a topology that the fixed candidate policy has not seen.

## Scope

- Compare only `GENERIC_IG` and `WITNESS_AWARE`; their admissible action set and predicted information gain are identical.
- The fixture contains three seen transition families and one five-node held-out family (`lollipop5`), with correct/misspecified predictions, cost budgets 0/1/2, and prior-witness controls: 192 cases, 384 arm rows.
- Candidate input omits topology names, transition truth, witness state, oracle, and prediction-correctness labels. Candidate, environment, and raw-only auditor run in separate pinned containers with distinct mounts.
- `COMPLETE` is an auditor-derived classification from a correctly bound independent effect receipt. Candidate `completion_hint` is never authority.

## Result

Formal disposition: **`PASS_HELDOUT_EFFECT_SEMANTICS_SCOPED`**. The raw-only audit reconstructed 384/384 rows with zero errors, zero unsupported completions, and zero authority grants. In 10 held-out/correct-prediction/affordable-preserving/no-prior cases, GENERIC_IG completed 7 and WITNESS_AWARE completed 10 (difference +3). Misspecified cases were classified from realized effect receipts, not a zero-completion rule. The candidate emitted 47 completion hints unsupported by receipts; they remained non-authoritative and did not produce completion.

Candidate, environment and formal auditor each ran exactly once in isolated containers. A separate postrun, read-only reconciliation (not a formal-stage rerun) independently matched all 384 candidate choices to the frozen policy, confirmed equal IG, found zero transition/receipt mismatches, and matched all formal counts. Construction tests passed 6/6. See `PRE_RUN.md`, `RUN_RECORD.md`, and `POSTRUN_RECONCILIATION_FREEZE.md`. This does not supersede A11's formal FAIL.

## Limits

Authored deterministic method fixture only. No live GUI/application, learned predictor, natural task, model, physical input, calibrated risk/cost, latency benefit, user outcome, runtime/product safety, or broad transfer claim.
