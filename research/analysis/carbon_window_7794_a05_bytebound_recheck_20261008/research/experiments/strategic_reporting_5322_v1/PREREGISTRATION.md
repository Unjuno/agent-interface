# Issue #5322 strategic reporting simulator — preregistration

## H — hypothesis

When a report influences routing and audit allocation, outcome scoring augmented by randomized audits reduces strategically harmful overclaiming versus metadata-only reporting, while preserving calibration, false-PASS rate, and legitimate UNKNOWN use. Peer prediction alone may reward agreement without truth. No game-theoretic equilibrium or authority claim is tested.

## T — one-shot synthetic test

Compare five advisory policies: `metadata_only`, `outcome_scoring`, `proper_score_random_audit`, `peer_prediction`, and `adversarial_audit`. Use seeds `269208469`, `490136210`, `794448238`; truth availability probabilities 0.95, 0.50, 0.15, 0.00; seven fixed scenarios: independent calibrated signals, disclosed common source, constant collusion, selective omission, false independence, responsive overclaim, and undisclosed shared error. Use 80 tasks per seed/regime/scenario and four agents per task; pair all policy arms on identical latent tasks and signals. This yields 6,720 tasks and 33,600 arm records.

Four binary verifiers have known reliabilities sampled uniformly from [0.55, 0.95]. Truth is equiprobable. One responsive verifier selects among truthful, overconfident, underconfident, constant, UNKNOWN, and omission strategies by the preregistered expected-utility rule. Remaining verifiers follow scenario-fixed strategies. The router returns PASS/FAIL only when at least two reports from distinct declared domains agree at confidence >=0.90; otherwise UNKNOWN. Audit budget is two reports per task. A natural outcome is available according to the assigned regime. Random-audit probability is 0.20; risk audit is capped by the same budget. Proper Brier reward weight is 4, route reward weight 0.02, peer agreement reward weight 0.15. UNKNOWN is never treated as a wrong outcome.

Signals are drawn before each policy arm and replayed identically in all five arms. The responsive verifier is agent 0. Its posterior is reliability when its signal is positive and one minus reliability otherwise. Each candidate action's expected utility is route reward `0.02 * 2 * abs(p - 0.5)` plus `4 * feedback_probability * (0.5 - expected_Brier)` in the outcome-scoring arms, plus `0.15 * expected_binary_peer_match` in the peer-prediction arm. The `UNKNOWN` action earns `0.30 * max(0, 1 - abs(q - 0.5)/0.20)`; omission earns zero. Ties keep the first action in the fixed order truthful, overconfident, underconfident, constant, UNKNOWN, omit. Feedback probability is natural truth availability, unioned with the marginal audit-selection probability in the randomized-audit arm. Each reporting candidate first enters an independent 0.20 lottery; if more than two are selected, two are uniformly sampled. The best-response calculation uses the exact marginal inclusion probability given the number of expected reporting candidates. In the adversarial arm, one peer report (agent 1–3) is uniformly sampled after commitment and its declared source is checked against the hidden source record; report 0 is not eligible. Source audits do not reveal outcomes to the scorer. Selection does not use the hidden source truth; only the post-selection audit comparison does. Audit evidence is post-report and cannot affect the report being scored.

The seven scenarios instantiate shared-source disclosure, constant collusion, selective omission, false independence, responsive strategy choice, or undisclosed common errors as their names indicate. Shared signals for agents 1–3 use one common binary draw at their mean stated reliability; agent 0's signal remains independent. `false_independence` and `shared_error_undisclosed` declare separate domains for that shared source; `common_source_disclosed` declares one shared domain. `constant_collusion` uses a shared source and fixed p=0.99 reports from agents 1–3. `selective_omission` omits agent 1's report when its posterior is within 0.18 of 0.5. `responsive_overclaim` makes agents 1–3 report 0.99/0.01 according to their signal direction. All other nonresponsive reports are truthful.

## D — decision gates

PASS only if proper scoring plus randomized audit reduces responsive overclaim rate by at least 0.15 versus metadata-only; does not worsen responsive Brier score; increases false PASS by no more than 0.01; reduces valid UNKNOWN rate by no more than 0.02; averages no more than 0.25 audited reports per agent slot; adversarial audit detects at least 0.30 of false-independence declarations; and independent audit reports zero errors while rejecting every frozen corruption control. Overclaim is preregistered as `abs(p - 0.5) >= abs(q - 0.5) + 0.20`; a calibrated response is not overclaiming merely because its posterior differs from 0.5. Rates are paired over all preregistered tasks; D gates compare the two named arms directly. Otherwise report FAIL for a violated numeric gate or UNCERTAIN if results are mixed or the synthetic utility assumptions decide the outcome. Any source/hash/raw-integrity mismatch is STOP; no formal retry.

## C — competing explanations

The utility scale and best-response action set may predetermine which strategy wins. Synthetic reports do not capture learning, monetary incentives, reputation over time, or strategic adaptation after seeing scores. Audit details and truth must not leak into the report decision except where the truth is naturally available before reporting; audits happen after report commitment. Agreement is not proof.

## U — limits

Synthetic finite one-shot best responses only. No real verifier/model behavior, equilibrium theorem, mechanism-design guarantee, runtime integration, safety authority, or product claim. Results can motivate a different experiment; they cannot authorize reports or actions.

## Freeze/execution

Freeze runner, independent auditor, tests, exact commands, and hashes before the sole formal run. Run on CPU; the experiment has no GPU computation. Formal output is append-only. Construction checks use no formal seeds. A fresh exact resource slot is required for a container allocation; absent that slot, do not start Docker or interfere with a queued allocation.
