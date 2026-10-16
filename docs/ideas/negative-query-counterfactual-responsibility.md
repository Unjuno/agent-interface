# Counterfactual responsibility for negative queries — #8624

- **Status:** Scoped finite-method result; live applicability remains unverified.
- **Source:** [Issue #8624](https://github.com/Unjuno/agent-interface/issues/8624), successor to [#5865](https://github.com/Unjuno/agent-interface/issues/5865); canonical method packet [PR #8739](https://github.com/Unjuno/agent-interface/pull/8739). Preserve the concurrent duplicate disclosure in [PR #8741](https://github.com/Unjuno/agent-interface/pull/8741) separately.
- **Idea:** After a scoped negative query has passed its completeness/freshness gate, diagnose which present or absent mutable facts make that result outcome-pivotal, including causes that matter only under a declared contingency. This is a diagnostic about a frozen rule model, not a live-screen causal claim or action policy.
- **Outcome:** The canonical finite T0 reported `PASS_METHOD_SCOPED` on an authored Boolean-rule model, including explicit absent-fact semantics, contingency-only causes, and `UNKNOWN_TOO_LARGE` when an explanation exceeded its declared budget. The method packet's independent enumeration supports only its finite cases. The separately retained concurrent duplicate result is not a replication and must not be pooled or used to strengthen the claim.

## Boundary and next question

Keep #5865's query-completeness and #8466's freshness checks as prerequisites; responsibility analysis cannot turn incomplete coverage into certified absence. Keep #7934's decision-value observation selection separate: it chooses what evidence to acquire, while #8624 explains a frozen query outcome. The open question is whether any real, defensible finite mutable-fact universe can be defined for visual queries. Until that is established, do not apply the synthetic toggle semantics to screenshots, authorize rescans, or attach runtime authority to responsibility scores.

The T0 method result is preserved in the PR record; no further formal run is proposed here. Any later GUI-applicability study needs a separate source, scope, owner, and prospective allocation.
