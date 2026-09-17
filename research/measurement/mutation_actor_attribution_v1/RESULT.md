# Result — #1211 mutation actor attribution

Decision: **PASS_MUTATION_ACTOR_ATTRIBUTION_SCOPED**.

- Formal invocation: 1; reruns: 0
- Records: 320,000 (80,000 each: self / external / unattributed / no-mutation)
- Candidate/oracle mismatches: 0
- LINEAGE_BOUND false self-credit: 0
- TEMPORAL_NEAREST false self-credit on non-self strata: 89,445
- Authority promotions: 0
- Task-success promotions: 0
- Independent audit: PASS
- Corruption controls: 12/12 rejected false SELF_CONFIRMED

Interpretation: exact mutation lineage is sufficient for this synthetic evidence-flow contract to distinguish self, explicit external actors, unattributed changes and no mutation. Temporal proximity alone produces false self-credit. This does not establish real actor detection, spoof resistance, semantic task success, or live GUI safety.
