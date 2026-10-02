# Issue #5428 T0 — wait-cost / option-loss monotonicity

Allocation: `REAL-OPTION-WAIT-COST-MONOTONICITY-5428-T0-20261003-01`  
Base: `main@b573071d821e20e818304200a9e6ec8c9bbf5670`  
Branch: `research/option-wait-cost-5428-t0-20261003`  
Path: `research/analysis/real_option_wait_cost_monotonicity_5428_t0_20261003/`

This is an additive exact-contract T0 under existing Issue #5428. It does not modify its prior model-gate FAIL, fixed-trace T2 PASS, or any predecessor record. No new Issue is needed for an allocation/harness correction under the repository's routing policy.

## H / T / D / C / U

**H.** After hard authorization, freshness, safety, and commit-window gates pass, the net pairwise rule `V_now = immediate_commit_value - lost_flexibility_cost`; `V_wait = future_best_gross_value - wait_cost`; COMMIT iff `V_now >= V_wait` has the required directionality: increasing only wait cost cannot change COMMIT to WAIT; increasing only lost-flexibility cost cannot change WAIT to COMMIT. A tie commits only when every hard gate passes. If values are not priceable/commensurable, the result is HOLD rather than invented arithmetic.

**T.** Deterministic Python standard-library enumeration, no model, GUI, network, container, GPU, or external action. Exhaustively evaluate the Cartesian grid `commit_value ∈ {-2,-1,0,1,2}` × `future_gross_value ∈ {-2,-1,0,1,2}` × `wait_cost ∈ {0,1,2}` × `lost_flexibility_cost ∈ {0,1,2}` (225 rows). Add ten frozen controls for missing authority, stale evidence, hard-safety failure, closed commit window, unpriceable uncertainty, expired wait window with commit still open, unavailable alternative wait route, tie, no new information with positive waiting cost, and useful information with negligible waiting cost. A separate auditor independently reconstructs all rows and matched counterfactual monotonicity chains without importing the candidate. Seven construction tests precede source freeze; after freeze, invoke candidate once and, only if it exits 0, auditor once. Retries = 0.

**D.** `PASS_METHOD_SCOPED` only if all 225 grid rows and 10 controls are present in order, the raw-only auditor independently reproduces every disposition, both monotonicity-violation counts are zero, hard-gate/unpriceable controls HOLD, tie commits under passed gates, and both wait-unavailable controls commit only when the commit window remains open. Any unsafe gate bypass or monotonicity violation is `FAIL_METHOD`; malformed/missing/mismatched evidence is `STOP_INTEGRITY`. Construction tests are not the formal result.

**C.** Integer utilities are an authored commensurable toy scale; exact pairwise comparison avoids probabilistic calibration but does not establish the values are measurable in an interface. The full finite grid supports local monotonicity checks only.

**U.** No empirical task, GUI, real deadline, user choice, signal quality, utility calibration, real reversibility, optimal-policy, latency, safety, or product conclusion. This checks a necessary decision-rule contract and cannot validate whether waiting is beneficial in practice.

## Frozen rules and run discipline

- Hard gates are evaluated before valuation; failure yields HOLD.
- If comparison is unpriceable, yield HOLD; do not infer an ordinal ranking from numeric placeholders.
- If the wait route is unavailable or its wait deadline has expired while the immediate commit window remains open, choose COMMIT; if the commit window is closed, HOLD.
- Equal net values choose COMMIT only after hard gates pass.
- No source, fixture, threshold, domain, or decision gate may change after `FREEZE.json` is written. Preserve the first formal raw and audit outputs; no reruns.
