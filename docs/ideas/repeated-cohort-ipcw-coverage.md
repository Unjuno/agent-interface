# Repeated-cohort IPCW uncertainty and interval coverage

- **Status:** A03 passed on one synthetic design/seed; predecessor outcomes remain separate.
- **Source:** Issue [#8049](https://github.com/Unjuno/agent-interface/issues/8049), successor to [#7993](https://github.com/Unjuno/agent-interface/issues/7993).
- **Idea:** Evaluate repeated-sampling uncertainty and interval coverage for a Horvitz–Thompson/IPCW estimator under a known two-stratum outcome/follow-up design.
- **Outcome:** A02 is a pre-container CLI STOP, not a result. Fresh-seed A03 `PASS_METHOD_SCOPED` reconstructed 20,000 cohorts / 8,000,000 units; HT mean was 0.250325, bootstrap coverage 0.94935, and 4/4 controls were rejected. This applies only to the declared synthetic model/seed and does not establish distribution-free coverage or live verifier calibration. Merged [PR #8116](https://github.com/Unjuno/agent-interface/pull/8116) preserves the result; A01 FAIL and A02 STOP remain.
