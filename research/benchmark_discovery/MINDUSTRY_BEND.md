# Bent-route calibration for the next Mindustry construction task

The next fixture adds a northward detour and a southward return to the receiving core. Eight targets replace the original six eastward tiles: (138,51,E), (139,51,N), (139,52,E), (140,52,E), (141,52,S), (141,51,E), (142,51,E), (143,51,E). The source and 112-tile surrounding guard remain fixed. Per-tile required rotations are explicit in mindustry_bend_plan_v1.json. The plan and cases were written before launch; the scorer was implemented during execution, so this is development calibration, not a preregistered implementation comparison.

Three fresh private Linux/Xvfb GUI processes loaded the pinned save. The fixture engine placed the conveyors, then ran a minimum 600-tick simulation window. These are engine-authored cases, not assistant construction actions. Before/constructed/after projections, final screenshots, source and asset hashes, stdout/stderr and cleanup evidence are retained in results/mindustry-bend-01.

| Case | Copper delta | Direction mismatches | Result |
|---|---:|---|---|
| Complete bent route | 33 | none | VERIFIED |
| East instead of north at (139,51) | 0 | (139,51) | CONTRADICTED |
| No conveyors | 0 | all eight targets | CONTRADICTED |

Every case preserves the surrounding 112-tile projection. Actual windows were about 600.19–600.79 ticks, not identical deterministic trajectories. Per-case setup plus simulation was 16.53–17.66 seconds, not planner speed or throughput evidence. Application processes were intentionally stopped after capture (return143), with no forced SIGKILL; all owned processes exited. Java/X11 ancillary diagnostics remain in raw records.

mindustry_bend_score_v1 layers exact per-tile direction checks over the existing placement/delivery scorer and validates positive finite window/goal values and complete unique direction coverage. Four offline controls verify rejection of a wrong direction even with positive recorded delivery, duplicate/missing direction definitions, and NaN duration. These controls do not prove a globally causal verifier. The independent audit checks pinned launch sources, image hashes, all three expected engine outcomes and four controls.

This calibration has only before/after phases. The next player-controlled episode must still use separate post-control delivery accounting and the validated three-phase window constraints from mindustry_build_score_v2. Do not substitute the two-phase calibration for construction-cost/delivery separation. Create a new player-ready empty-route entry, combine direction checks with the three-phase scorer, then perform screenshot-guided construction with no engine-authored conveyors. No formal benchmark adoption or broad planning skill is established yet.
