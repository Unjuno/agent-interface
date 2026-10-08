# V39 current-main cancel race boundary test — 2026-10-08

Source commit: `f59b2494f403b33349cbf202b49d76caef3d6d82`.
Source file is an exact Git blob export from `research/doom/map01_overlap_controller_v39.py`; isolated AST extraction executes only `cancel_invalidated_cover()` to avoid importing model/game/runtime dependencies. No controller or test source in the working tree was modified.

Question: does current-main cover invalidation interrupt the pending planner and accept a terminal result only when cancellation or a natural completion/expiry race is paired with verified empty key/button state?

Result: 3 focused boundary tests passed. The normal cancelled state and natural `completed`/`expired` states pass with verified empty releases. Held keys, unverified release, `failed`, `needs_decision`, and missing release reject. This is a source-contract unit probe, not an integrated controller run.

It does not test a live game, current screenshot during a model wait, typed HUD change, threat exposure, model interruption behavior, useful feedback, gameplay recovery/progress, terminal outcome, or #59 acceptance. The live allocation gate remains unassigned per the latest #59 owner record and #6957 integration checkpoint. Prior A04 is consumed and remains unchanged.

`test-output.txt` and `test.exit` retain the first test result. `SHA256SUMS.txt` covers all five frozen files.
