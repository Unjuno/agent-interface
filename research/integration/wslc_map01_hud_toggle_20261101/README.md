# MAP01 HUD visibility toggle and fixed-template review

Two fresh isolated WSLc episodes test the configuration difference observed between the old HUD template probe and the newer watch runs. The same 316-file candidate was used except for one explicit game-initialization setting, `set_render_hud(False)` in et01 and `set_render_hud(True)` in et02. Both use the same scripted 500 ms fire/threshold-32 watch, seed 991039, no model, private Xvfb, 1 CPU / 1 GiB and network none, in off/on order. This is a game setup API setting, not an in-game user action. Seed and HUD settings are recorded by conditions and launcher rather than independently read back from the simulator.

| allocation | setting | exact old HUD template before / end | adjacent ammo samples | action and release |
|---|---|---|---|---|
| et01 | HUD off | unknown / unknown | 50→49 | watch cancelled; partial effect unknown; release verified |
| et02 | HUD on | 50 / 49 | 50→49 | watch cancelled; partial effect unknown; release verified |

Both had one hit, 15 damage, no kill and health 100→94 between the pending-start and model-done fixture samples, with tested keys up at close. Samples and screenshots are adjacent, not atomic, and counters do not prove the effect of a specific input. The on screenshot visibly contains the status bar; the off screenshot does not. The old 50/49 templates are compared byte-for-byte, not via the simulator. This demonstrates a concrete configuration-dependent observation seam and a useful fixed-layout positive control, not reliable arbitrary-value recognition, safe automatic configuration changes or production recovery.

`public.zip` retains conditions, candidate, prior manifest/runner, fixed templates, screenshots, monitor crops, fixture messages, receipts and counters. Run `python research/integration/wslc_map01_hud_toggle_20261101/audit.py` from a Git checkout containing commit f2bd781bfb88f5d24b43cb016ad90183b2156e05, without -O and with Pillow. The auditor checks all archive hashes, verifies that the candidate differs from the prior manifest only in the explicit HUD setting, binds templates to the old pinned archive, recomputes patch changes and template matches, and verifies action/release/counter records. Private path-bearing launcher commands are omitted and not independently audited. WSLc reported no active allocations after the run.

This is one fixed-order pair with independent game evolution, fixed resolution, target, seed and values. The watcher is not semantic threat detection, timing is not a bound, and no model, task-completion or MAP01-exit claim follows. WSLc warned that the memory limit excludes swap.
