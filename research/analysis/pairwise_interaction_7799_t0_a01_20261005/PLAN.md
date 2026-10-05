# Issue #7799 T0 — pairwise-interaction eligibility

## H — hypothesis

The selected Issue #57 integration path contains at least one pair of individually characterized, independently switchable mechanisms whose four 2×2 cells can be executed through the same caller, workflow, reset, scorer, and accounting path without changing authority semantics.

## T — minimum test

Read-only audit of exact main `b5be19963454ce5edafc945b78b100012952dd15`: inspect the selected integration plan and its enforcing three-arm protocol. Encode the two most directly co-selected mechanisms—compiled symbolic representation/target handles and local continuation—as binary factors, then enumerate the required `(0,0)`, `(1,0)`, `(0,1)`, `(1,1)` cells. Independently recompute the cell coverage and rank of the interaction design matrix from the candidate's raw facts. No GUI, model, effect, task input, or runtime execution is part of T0.

## D — decision

- `PASS_T0_ELIGIBLE` only if both factors are independently operable in the selected path and all four cells are specified by the same caller/workflow/scorer/accounting contract.
- `HOLD_T0_NO_ELIGIBLE_INDEPENDENT_PAIR` if the existing selected path couples the factors or omits a required cell. This is not a finding of zero interaction and does not reject Issue #7799.
- `FAIL_T0_AUDIT` if the independent checker cannot reproduce source identities, arm coding, cell coverage, or the decision.

## C — competing explanation

A different pair among individually characterized methods might be eligible, but selecting it would add a mechanism expressly excluded from the chosen #57 bundle. The issue's bounded one-pair design may still be useful after the #57 bundle changes or a compatible four-cell caller is independently qualified.

## U — limits

This is a source-bound eligibility check only. It estimates no outcome, interaction, correctness, token, latency, or task effect. The result applies to the selected #57 path and exact pinned main, not to every repository mechanism or future integration.
