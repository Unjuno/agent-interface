# Result

Decision: **PASS_DECISION_POLICY_ACTION_GUARD_SCOPED**

- Formal scenarios: 250,000
- Action slots/scenario: 19
- Guarded hard-invalid effects: 0
- Guarded ambiguous effects: 0
- Supervisor-only hard-invalid effects: 750,459
- Supervisor-only ambiguous effects: 250,000
- Candidate/oracle mismatch: {'guard_vs_oracle': 0, 'redecide_vs_oracle': 0}
- Pre-hard valid guard/reference mismatch: 0
- Semantic decisions: guarded cache 250,000 vs re-decide 4,750,000
- Authority grants: 0
- Formal invocations/reruns: 1/0
- Independent audit pass: True

Interpretation: at the frozen 20 ms supervisor cadence, between-sample hard/ambiguous windows produced forbidden effects in the supervisor-only control. Per-action exact current evidence eliminated those effects in the synthetic mechanism while retaining cached semantic decision reuse until the first hard invalidation. This does not measure real evidence-acquisition cost, model tokens, or live planner-gap latency.
