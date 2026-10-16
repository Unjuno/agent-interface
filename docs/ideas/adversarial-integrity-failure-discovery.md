# Adversarial integrity in privacy-preserving failure discovery

- **Status:** Unverified synthetic feasibility proposal.
- **Source:** [Issue #8877](https://github.com/Unjuno/agent-interface/issues/8877), successor to #6549.
- **Idea:** Hold the privacy mechanism, cohort, failure-class vocabulary, and release thresholds fixed, then vary bounded adversarial contribution power to test whether a coalition can fabricate classes, suppress genuine classes, or change the privacy–utility frontier.
- **Outcome:** No experiment or current telemetry-poisoning finding is reported. The proposed discriminator concerns integrity under adversarial participation, distinct from #6549's privacy-constrained discovery feasibility and its retained prior result.
- **Boundary:** Any future result would be limited to its synthetic contribution and threat model; it would not establish fleet telemetry safety or deployment readiness.
