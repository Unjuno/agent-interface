# Persistent geometric state role-safety — Issue #1560

Task: `PERSISTENT-GEOMETRIC-STATE-ROLE-SAFETY-20260918-001`

This experiment tests storage/typing integrity only. It does not test whether persistent world memory improves Astra, context compaction, tokens, latency, or task success.

The frozen contract persists geometry plus role/freshness/provenance. Stored evidence has no input or semantic authority. Direct actuator admission requires a live `ADMISSION_DEPENDENCY(CURRENT)`. A historical `HINT` can contribute only through explicit `REVALIDATE_CURRENT` with fresh current `PLANNER_CONTEXT`, producing a distinct current admission receipt; the historical record remains unchanged.

Formal: directed role×freshness×roundtrip matrix plus 20,000 fixed-seed randomized state/operation sequences. Any weak/historical/expired backend emission, role escape, or provenance mutation is a hard failure.
