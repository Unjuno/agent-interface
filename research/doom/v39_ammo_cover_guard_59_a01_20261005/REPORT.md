# Issue #59 A01 — ammo depletion during renewable fire cover

## Outcome

`FAIL_AMMO_DEPLETION_NOT_GUARDED` for the frozen synthetic guard-boundary gate. The current-main v39 cover monitor did not request a new decision when a notional active `fire` cover's typed ammo changed from 4 to 0 while health remained 100 (authored hard minimum 90). The unchanged-positive-ammo control preserved the policy, and the health=89 control correctly requested a new decision. The independent audit reconstructed all 7 checks.

This is consistent with source wiring: `build_cover_monitor` binds the renewable-cover monitor to the health reader; ammo is extracted separately for immediate action validity. The responder prompt explicitly permits `fire` in `next_cover` only when a threat is visible and ammo remains at policy-authorship time. The experiment did not run the full controller and did not observe an actual fire pulse or renewal.

## Evidence and reproducibility

- Frozen current-main commit: `109cedcf1fafc150e235c91141eb47bbc7396b43`.
- Candidate/probe invoked once; independent arithmetic audit invoked once; formal live allocation 0; retries 0.
- Fixture: `fixture.json`; source manifest: `FREEZE.json`; result: `RESULT.json`; audit: `AUDIT.json`.
- Reproduce in this checkout with `PYTHONPATH=research/live_control python3 -B research/doom/v39_ammo_cover_guard_59_a01_20261005/probe.py` followed by `python3 -B research/doom/v39_ammo_cover_guard_59_a01_20261005/audit.py`. The probe refuses an existing result.
- Hashes are in `SHA256SUMS`. Frozen source hashes were checked before execution.
- OrbStack 29.4.0 was reachable, but read-only image inventory failed on a cached containerd blob (`operation not supported`). No pull/build/repair/restart was attempted. The tested guard/monitor boundary is stdlib-only; host CPython 3.14.5 ran the exact functions without an isolation claim.

## Limits and next experiment

The result does not establish whether zero-ammo fire actually consumes an input pulse in MAP01, whether a typed ammo event arrives before renewal, whether cancellation releases keys correctly, or whether ammo depletion harms survival/progress. Do not change the frozen v39 path based on this synthetic result alone. A successor should first test a bounded ammo predicate in an isolated construction and mutation suite; a live evaluation needs a separately assigned lane and must measure typed-ammo observation, invalidation, cancel/empty-release, and independently scored progress under a fresh freeze.
