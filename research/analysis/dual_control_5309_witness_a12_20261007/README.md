# Issue #5309 A12 — held-out effect semantics

This is a new, main-based allocation. It does not modify A04–A11 evidence or reinterpret A11's formal FAIL. The question is whether a raw-only scorer can distinguish model prediction correctness from realized, independently witnessed task effect on a topology that the fixed candidate policy has not seen.

## Scope

- Compare only `GENERIC_IG` and `WITNESS_AWARE`; their admissible action set and predicted information gain are identical.
- The fixture contains three seen transition families and one five-node held-out family (`lollipop5`), with correct/misspecified predictions, cost budgets 0/1/2, and prior-witness controls: 192 cases, 384 arm rows.
- Candidate input omits topology names, transition truth, witness state, oracle, and prediction-correctness labels. Candidate, environment, and raw-only auditor run in separate pinned containers with distinct mounts.
- `COMPLETE` is an auditor-derived classification from a correctly bound independent effect receipt. Candidate `completion_hint` is never authority.

## Current status

Pre-run construction suite: 6/6 passed. Container image, read-only input mount, and writable output mount smokes passed. Formal candidate/environment/auditor invocations have not yet run. See `PRE_RUN.md` for the frozen hypothesis, gates, exact commands, and hashes; see `RUN_RECORD.md` after the one-shot execution.

## Limits

Authored deterministic method fixture only. No live GUI/application, learned predictor, natural task, model, physical input, calibrated risk/cost, latency benefit, user outcome, runtime/product safety, or broad transfer claim.
