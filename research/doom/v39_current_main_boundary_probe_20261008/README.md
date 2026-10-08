# V39 current-main cancel race boundary test — 2026-10-08

Source commit: `f59b2494f403b33349cbf202b49d76caef3d6d82`.
The packaged source is an exact byte-for-byte Git blob from commit `f59b2494f403b33349cbf202b49d76caef3d6d82`, verified against its tree object. Isolated AST extraction executes only `cancel_invalidated_cover()` to avoid importing model/game/runtime dependencies. No runtime source was modified.

Question: does current-main cover invalidation interrupt the pending planner and accept a terminal result only when cancellation or a natural completion/expiry race is paired with verified empty key/button state?

Result: 3 focused boundary tests passed. The normal cancelled state and natural `completed`/`expired` states pass with verified empty releases. Held keys, unverified release, `failed`, `needs_decision`, and missing release reject. This is a source-contract unit probe, not an integrated controller run.

It does not test a live game, current screenshot during a model wait, typed HUD change, threat exposure, model interruption behavior, useful feedback, gameplay recovery/progress, terminal outcome, or #59 acceptance. The live allocation gate remains unassigned per the latest #59 owner record and #6957 integration checkpoint. Prior A04 is consumed and remains unchanged.

`test-output.txt` and `test.exit` retain the first test result. `SHA256SUMS.txt` covers all five frozen files.

## Additional current-main regression

Using the exact-main sparse worktree (`f59b2494f403b33349cbf202b49d76caef3d6d82`), the existing focused V39 suites were run on 2026-10-08:

`python -m unittest -v test_map01_overlap_controller_v39 test_map01_overlap_controller_v39_dual_signal test_map01_overlap_controller_v39_pair_duplicate_consistency`

Result: 26 tests passed, exit 0. Coverage includes natural-terminal invalidation races and empty release, rejecting unsafe release evidence, paired health/ammo epoch and binding consistency, out-of-order/duplicate observations, unavailable or zero ammo on fire covers, and safe soft ammo feedback. This remains component/regression evidence; it does not invoke Doom, model inference, GUI observation or OS input and cannot satisfy the live gate.

Raw output is `current-main-regression-output.txt`; exit is `current-main-regression.exit`.
## Expanded exact-current-main regression

Source main: `4c203d797cd3e33168bd9177fea8e0d6ef605c6b`. The following six existing suites were run from repository root against tracked current-main files:

`python -m unittest -v research.doom.test_map01_overlap_controller_v39 research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_overlap_controller_v39_wait research.live_control.test_action_validity_admission_v1 research.live_control.test_observable_signal_guard_v2`

Result: 42 tests passed, exit 0. This adds wait-loop precedence/observation-before-terminal handling, typed invalidation propagation, action freshness/admission, and source-bound guard coverage to the earlier 26-test subset. Raw output is `current-main-regression-output.txt`, exit in `current-main-regression.exit`, source in `current-main-regression.source`.

These are local deterministic regression tests. No actual Doom process, model request, game clock, GUI, or OS input ran; live threat exposure, physical release, useful effect, recovery, progress and MAP01 terminal outcome remain unverified.


