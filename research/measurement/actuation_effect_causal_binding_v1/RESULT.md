# Result — #1283 actuation/effect causal binding

Decision: **PASS_ACTUATION_EFFECT_CAUSAL_BINDING_SCOPED**.

- 320,000 traces = 4 immutable batches × 80,000.
- Candidate / independent oracle mismatches: 0.
- Actuation-bound false self-credit: 0.
- TIME_ONLY (<=500 ms) false self-credit: 128,000.
- Exact SELF_EFFECT: 64,000 = 32,000 ordinary self + 32,000 delayed-but-explicitly-bound self.
- UNATTRIBUTED_EFFECT: 224,000.
- NO_EFFECT: 32,000.
- Authority promotions: 0.
- Batch reruns/replacements/tuning: 0.

Scoped conclusion: exact input-side actuation lineage is not sufficient to credit an independently observed task effect by timing alone. The effect receipt must itself bind the actuation identity (plus session/target/effect kind and causal order) to avoid the tested external/other-actuation/conflict/mismatch laundering paths. This does not authenticate the effect receipt producer; live scorer separation remains a successor requirement.
