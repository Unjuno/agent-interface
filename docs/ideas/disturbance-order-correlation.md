# Disturbance-order correlation under equal exposure

- **Status:** Synthetic method result passed; workload transfer remains unverified.
- **Source:** Issue [#8434](https://github.com/Unjuno/agent-interface/issues/8434), successor to [#6604](https://github.com/Unjuno/agent-interface/issues/6604).
- **Idea:** Match marginal disturbance exposure while varying its temporal order (IID, clustered, alternating, and held-out blocks) to test whether history dependence changes route comparisons.
- **Outcome:** T0 A01 `PASS_METHOD_SCOPED` on 96 authored cases, with a single candidate and raw-only auditor and zero reconstruction errors. Held-out paired deltas (switch-reconfigure minus two-step-cache) were IID −10, clustered +21, alternating −31, and held-out blocks +27. This shows schedule sensitivity in the frozen synthetic fixture only, not general workload difficulty, a real route effect, or GUI benefit. Merged [PR #8442](https://github.com/Unjuno/agent-interface/pull/8442) preserves the result.
