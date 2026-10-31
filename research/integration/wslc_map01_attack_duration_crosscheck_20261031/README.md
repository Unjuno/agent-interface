# MAP01 retained-evidence crosscheck: attack duration and effects

This is an analysis of existing raw data, not a new experiment. `audit.py` pins both source archives by SHA-256 and recomputes ammunition, kill count, selected visible labels, action wait and final release for the wait/1,000 ms attack arms of `wslc_map01_model_ammo_control_20261031` and the two 500 ms attack arms of `wslc_map01_pending_change_control_20261031`.

| Allocation | Intervention | Ammo: before / immediate / final | Kills: before / immediate / final | Selected immediate labels |
| --- | --- | --- | --- | --- |
| af01 | wait 1,000 ms | 50 / 50 / 50 | 0 / 0 / 0 | Zombieman |
| af02 | fire 1,000 ms | 50 / 47 / 47 | 0 / 1 / 1 | Blood, DeadZombieman |
| ai01 | fire 500 ms | 50 / 48 / 48 | 0 / 0 / 0 | Blood, BulletPuff, Zombieman |
| ai02 | fire 500 ms | 50 / 49 / 48 | 0 / 0 / 0 | Blood, Zombieman |

All four observed the final tested keys up and verified owner release. In ai02 ammunition declined again between the immediate and first passive sample; immediate sampling alone would miss part of the game response. The simulator's labels support a more detailed description of its rendered/game state, but `Blood` alone is not an independently verified hit, attribution to a specific shot, or proof of damage. The count and visible dead-enemy label corroborate a game-reported kill for af02 only.

These results suggest duration and post-release effects merit a controlled follow-up; they do not show that duration caused the kill difference. These arms came from different experiments, at fixed order, with separate model decisions, different elapsed game states and potential effects from the earlier interrupted input. The 1,000 ms pulse in af02 was predeclared by the experiment, whereas its model proposed 500 ms. Comparing these observations does not establish a reliable optimal duration, safety, model speedup, or MAP01 completion. In the newer runner, model target coordinates are used to validate a patch and a center constraint; they do not themselves turn the player toward the target. This limits what the shot can demonstrate about model-directed aiming.

A discriminating future study would preregister repeatable 500 ms and 1,000 ms interventions plus wait, record ordering and seeds, hold the initial game state as closely as possible, retain the same scorer and post-release window, and measure game-reported damage/kill separately from key release and ammo. Its allocation, stop rules and conditions must be frozen before execution; the present retrospective observations are not a substitute for that comparison.

Run `python audit.py` from this directory (or any cwd) in a checkout containing both referenced source directories; no third-party package is needed. Raw screenshots, configuration, responses and full sample traces remain in the two original archives.
