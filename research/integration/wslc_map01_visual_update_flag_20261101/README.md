# MAP01: simulator update flag and visual review

Four sequential fresh WSLc allocations compare `advance_action(1, False)` and `advance_action(1, True)` immediately before each screenshot, crossed with an 85 ms post-watch fire or withhold. Conditions and order were frozen before the first run; all used the same fixed seed, HUD, local image, 600 ms cooperative review budget and exact 49/48 pixel templates from the preceding refresh-control experiment. The scorer's `sample()` also advances the simulator, including immediately before and after review. The controller receives no simulator score. `advance_action` is a privileged simulator operation, not a general screen refresh API.

| Allocation | Update state | Follow-up | Visual review | Frames | Review duration |
|---|---|---|---|---:|---:|
| ey01 | false | fire | timeout / unknown | 8 | 670.09 ms |
| ey02 | true | fire | exact 48 | 2 | 156.76 ms |
| ey03 | true | withhold | timeout / unknown | 7 | 600.44 ms |
| ey04 | false | withhold | timeout / unknown | 8 | 669.27 ms |

In ey01 the adjacent simulator sample already reported ammo 48 before visual review, while every review crop remained 49. In ey02 the pre-review sample reported 49, and the 48 template appeared during review. Both withhold controls remained 49 in simulator samples and images. The original monitored fire was cancelled with unknown effect; the old alias was refused and no replay occurred. All final releases were verified, and all four private fixture processes exited successfully. The loop's budget is cooperative: individual calls can overrun it, as the 670 ms results show.

This small fixed-order, fixed-seed comparison shows a difference in these runs, not a general causal guarantee or real-time solution. The update call can change the game timeline, and the adjacent sample also advances it. The 48 template was derived from a prior same-scene run, and a single positive per condition cannot establish reliability, enemy hits, task completion, or speed versus a model-driven baseline. The cancelled original fire's effect remains unknown.

The existing `observation_worker` is not a drop-in bound for this review: `NativeHandleBridge._isolated_observation_active()` requires both an active program and its deadline, and the review calls `bridge.observe()` after the action has completed. The existing worker documentation explicitly says idle observation remains synchronous. A bounded idle-review design needs its own deadline and ownership/late-result fencing; merely turning on the active-program worker would not establish the bound. Moreover, bounding capture alone would not bound the preceding privileged simulator call or guarantee operating-system scheduling.

`public.zip` retains candidate sources, frozen manifests and conditions, screenshots, simulator samples, host/container logs, and results; SHA-256 `1b09774d3a0cd758f63130bdda11f63a1eaa8c07f26e4d440cc132d737ded912`. From a checkout containing commit `8d1a583`, run `python research/integration/wslc_map01_visual_update_flag_20261101/audit.py` without `-O` (Pillow required). The audit checks archive and previous candidate provenance, the exact one-line intervention, control assignment, original policy gate and monitor image differences, cancellation and releases, visual crop hashes, selected simulator samples and final screen. Raw scorer samples are retained for independent inspection. No new public live-control or model-performance claim is made.
