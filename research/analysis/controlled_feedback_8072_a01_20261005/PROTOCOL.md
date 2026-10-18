# #8072 T0 — controlled-feedback finite simulation

## H / T / D / C / U

**H.** On a deliberately finite task world with both transferable strata and exact-ID traps, withholding per-task feedback while disclosing every planted hard failure prevents the adaptive learner from overfitting its development cohort, without more than 5 percentage points of fresh-cohort utility loss versus a generalizable comparator.

**T.** Run 100 preregistered seeds. Each seed has a fixed development cohort and disjoint fresh cohort from the same generator. The same eight-query adaptive update loop runs under (a) FULL: exact row outcomes; and (b) CONTROLLED: aggregate utility only, accepted only when the gain is at least two development rows. A hidden hard-safety flag is a separate exact channel in both arms and vetoes candidate promotion. Fresh rows are not read until the selected candidate is locked. A separate raw-only auditor recomputes all outcomes, proposal decisions, vetoes, and final disclosure. No model, GUI, user data, network, or runtime authority.

**D.** `PASS_METHOD_SCOPED` requires exact independent reconstruction, lower median development-to-fresh optimism for CONTROLLED, fresh utility no more than 0.05 below FULL, all planted hard-safety failures exactly disclosed and vetoed, zero pre-lock fresh reads, and complete post-lock disclosure. Otherwise report `FAIL_METHOD` or `HOLD` by failed gate. These are criteria for this authored finite world only.

**C.** The result may be caused by the hand-designed learner/update rule, threshold, feature structure, or candidate family; detailed diagnostics may be essential for real discovery. The two-row threshold is not calibrated to a real evaluation suite.

**U.** This cannot establish actual researcher behavior, GUI generalization, safe leaderboard design, differential privacy, or value of concealing real task outcomes. Safety vetoes here are synthetic booleans, not runtime safety controls.

## Frozen mechanics

Each task has a stratum and a unique development-only trap identity. The baseline is correct on half of rows by construction. A `PATCH_ID` proposal repairs only one currently failing development row. A `TRANSFER_STRATUM` proposal repairs every row in one selected stratum and is evaluated against fresh rows as well. FULL uses its row-level errors to select `PATCH_ID`; CONTROLLED has only an aggregate response and selects the next stratum in a fixed cyclic order. Both receive eight proposals and use the same accept-if-feedback-allows update rule. The scorer sets hard-safety regression on a planted proposal independently of utility; both policies receive that exact signal before any accept decision.
