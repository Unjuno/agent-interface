# A02 base freshness deviation

The frozen package records local `origin/main` at `02e0b19838ef87dba421480154314fa07b00a386`, committed at 2026-10-04 19:11:46 UTC. GitHub's authoritative commit API shows `d1a19b6929569a291c210a680c7e22c31732b949` was committed to main at 19:15:04 UTC, before this package froze at 19:18:54 UTC. Therefore A02 did not satisfy the preregistered "current main" source-base requirement.

The candidate's local sensor API is read-only and its complete source/SDK identities remain frozen. Preserve the measured six-sample result and its raw audit, but retain the protocol-level disposition `HOLD_BASE_SNAPSHOT_STALE`. Do not rewrite the freeze or repeat the sensor read as a repair. Any later construction must use a new identity, fresh main, and its own preregistration.
