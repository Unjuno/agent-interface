# #8914 T0 A02 preregistration

Status: frozen CPU-only synthetic method test. No live replay, GUI, game, model/provider call, WSLc, Docker, or shared-runtime allocation.

## Question and estimand

Under a fixed deep-repeat budget, do a preregistered metadata ranker or a feature ranker trained only on shallow observations discover more injected hidden failures among held-out-family cells with zero shallow failures than uniform allocation? The estimand is finite-fixture discovery yield, not population failure probability, safety, calibration, or certification.

## Frozen design

- Four train families and four disjoint evaluation families; family identity is never a ranking feature.
- Training cells contain shallow trials and may contain failures. Evaluation cells are eligible only after exactly two shallow trials both report no failure. Each family has a frozen set of binary metadata/features and latent propensities generated from seed 8914.
- Three arms use the same 200 deep attempts and a common 20% random-sentinel allocation: uniform over eligible cells; simple metadata rank (risk bit); feature rank learned from training-family shallow labels using smoothed feature-group rates. Ties use lexical cell ID. Remaining attempts go to the top-ranked half in equal round-robin order; uniform uses equal round-robin over all eligible cells.
- Signal world has a stable feature/risk relationship across disjoint families; null world has no feature effect. Family-shift world reverses the relationship in evaluation families. All worlds are generated before outcome reveal from fixed seeds listed in `freeze.json`.
- Every attempt has a unique `(world, arm, cell, repeat)` identity and a reset token whose expected hash is independently recomputable. A reset mismatch makes that attempt ineligible and held; it does not become a sample.
- Candidate sees only schema-checked shallow records and frozen metadata. It never receives deep outcomes. Runner uses a deterministic counter-based PRNG for deep outcomes, independent across repeat identities.

## Decision rules

`PASS_METHOD_SCOPED` requires: exact independent reconstruction of all denominators, arms, sentinel and adaptive allocations, outcomes and reset receipts; all candidate/audit corruption controls rejected; signal-world feature arm discovers more hidden failures than uniform at equal eligible budget; and the null-world paired mean lift's two-sided 95% interval includes zero and its upper bound is at most 0.05 failures per attempt. Family-shift performance is reported without a pass requirement. Otherwise report the precise FAIL/HOLD and preserve raw; do not tune or rerun this allocation.

A discovery difference is not a calibrated risk estimate. Sentinel yield is reported separately. Reset-failed or malformed attempts remain in the ledger as held and do not enter the eligible denominator.

## Frozen controls and limits

Controls: null signal, held-out family shift, unexpected deep-outcome key in candidate input, duplicate repeat identity, and reset-hash mismatch. The audit must reject each mutated copy. Synthetic Bernoulli outcomes do not model provider drift, correlated failures, application state, evaluator error, or real reset reliability. No live safety or GUI claim follows.


## A02 lineage note

A01 was consumed at `FAIL_AUDIT` before scientific gates because runner and auditor used different eligible-cell order for sentinel reconstruction. A02 is a new allocation with a new seed and a frozen, sorted eligible-cell order shared by the generation and audit contracts. No A01 outputs or candidate results are reused.
