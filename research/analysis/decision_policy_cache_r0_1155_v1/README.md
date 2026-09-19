# Decision-policy cache R0 (Issue #1155)

H/T/D/C/U: a bounded cache reuses an already-authored decision while current evidence is VALID; HARD invalidation stops, AMBIGUOUS yields, and ordinary replanning resumes. The finite trace compares redecide-every-cycle with cached deterministic monitoring. PASS_DECISION_POLICY_CACHE_R0_SCOPED: identical effect sequence, zero stale continuation, zero hard-invalid continuation, one ambiguity yield, and 3 vs 7 semantic decisions. This is synthetic semantics only; no model, GUI, network, task input, or runtime claim.
