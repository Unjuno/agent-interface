# Session-bound scorer attribution T0 v2 — result

The frozen #7537 v1 candidate returns `TEMPORALLY_UNIQUE` for a fixture whose scorer records are from `run-b` while the only verified input interval is from `run-a`; both use overlapping numeric timestamps. This is an API-boundary counterexample: the v1 record contract does not contain or validate session identity. It does not show that any retained live dataset is actually mixed across runs.

The additive v2 wrapper requires a non-empty, identical `session_id` on every sample, event, and actuation interval before delegating to the unchanged v1 timing algorithm. It refuses the cross-session join and missing IDs, while preserving the same-session fully bracketed result. The result remains `TEMPORALLY_UNIQUE`, not causal attribution.

Verification: v2 adversarial suite 4/4 PASS, including the v1 false-join control; parent v1 suite 9/9 PASS; parent T0's six cases and independent saved-result audit PASS; `git diff --check` PASS. These are local host CPU construction checks, not container or live results.

**Interpretation:** session identity is now an explicit prerequisite for temporal association. Its authenticity and the common clock's provenance must still be bound by a future live collector. No useful task effect, recovery, safety, survival, or MAP01 outcome is established. The #59 live allocation remains unassigned.
