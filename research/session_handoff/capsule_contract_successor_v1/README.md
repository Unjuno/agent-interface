# Authority-safe handoff capsule contract (successor #2630)

Pure contract construction for #2630. The validator accepts only a complete, session/task-matching, bounded-expiry capsule whose uncertainty is explicit, replay is prohibited, and authority status is `FRESH_ACQUISITION_REQUIRED`. It returns `ADVISORY_ONLY`; it never grants authority. Missing, stale, overlong, contradictory, mismatched, or authority-granted capsules return `UNKNOWN`.

Local finite matrix: 8/8 expected outcomes, network-free, no model/planner/GUI/input/provider call. Digest: `5b6c70774c6e0c19c85f959326104f7537bb7d2816cd222ad61e7a6e0f94e59a`.

This is contract construction, not live handoff, fresh authority acquisition, two-domain recovery, latency, token, or task-correctness evidence.
