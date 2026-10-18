# V39 current-main cancel race boundary test — 2026-10-08

This is a historical package: “current main” below refers to the named source at execution time, not today's main. Allocation/ownership statements are historical as well. They do not authorize a new launch.

Source commit: `f59b2494f403b33349cbf202b49d76caef3d6d82`.
Source file is an exact Git blob export from `research/doom/map01_overlap_controller_v39.py`; isolated AST extraction executes only `cancel_invalidated_cover()` to avoid importing model/game/runtime dependencies. No controller or test source in the working tree was modified.

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


Optimized execution: the same six suites were also run with `python -O`; 42 tests passed, exit 0. Raw output and exit are `current-main-regression-optimized-output.txt` and `current-main-regression-optimized.exit`. This confirms this focused regression set under optimized CPython; it does not add live behavior evidence.


## Planner-to-release boundary suites

On exact current main `4c203d797cd3e33168bd9177fea8e0d6ef605c6b`, the existing `persistent_planner_adapter_v2`, `final_action_admission_v2`, and `executor_v13` suites passed 30/30 normally and 30/30 under `python -O`. Raw outputs and exit codes are retained as `planner-release-{normal,optimized}.txt/.exit`. They cover interrupt/completion races, stale answer refusal, action admission and executor release-terminal custody. No live inputs or game were used.

## Recovered historical receipts for 708ca (published 2026-10-15)

Previously unpublished local outputs pin source `708ca59a8128f07fdb7e13a36704c6b2f79c9fb6`. The same six controller/typed-observation/admission suites above report 42 tests passing normally and under `-O`; the same three planner/release suites report 30 tests passing in each mode. Four raw output files, four zero exit files, two source-pin files and their original checksum list are now retained under `current-main-708ca-*`. All ten listed hashes match; raw bytes are preserved without line-ending conversion. [The publication receipt](PUBLICATION_708CA_20261015.json) records their identities and custody limits.

This is publication of saved component-test evidence, not a fresh execution, live allocation or proof that the historical executing worktree was pristine beyond its retained source declaration. It does not establish physical release, useful feedback, recovery or MAP01 completion. The current controller/planner/release suites were separately run on main `4062116ea4d70f1904cdea9669c8c2226acd7b9d` on 2026-10-15: 98 tests passed normally and under `-O`. That fresh result has the same component-level scope.

