# Mindustry pinned-save reset feasibility

Two cohorts now preserve a canonical Fork save and **four fresh GUI reloads**
of those exact bytes. All four reloads match the creation-time oracle for all
75,000 tiles (floor, block, overlay, team, nullable building rotation), dimensions,
wave, core presence, and copper=200. All four reload screenshots have the same
SHA-256; original-resolution inspection shows the paused core view and build UI.
This resolves the previously observed terrain variation for this saved fixture's
measured projection. It does not qualify a gameplay benchmark or shared interface.

## Evidence and interpretation

- [Cohort 01](results/mindustry-reset-01/audit.json): one save creation and two
  fresh HOME/XDG/Xvfb/Openbox/Java reloads using `mindustry_reset_v1.py`.
- [Cohort 02](results/mindustry-reset-02/audit.json): two additional fresh reloads
  using the explicit `--save` path in `mindustry_reset_v2.py`.
- [Canonical save](results/mindustry-reset-01/canonical.msav): SHA-256
  `8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed`.
- Reload setup-to-oracle-ready times: 7.597, 8.206, 8.298, 7.100 seconds.
  These are application setup observations, not model latency or speed comparisons.
- Five application processes exited after SIGTERM without SIGKILL; all owned
  processes were reaped. Four successful reloads cannot estimate reliable reset
  rates or establish crash recovery.

The save-creation screenshot differs from the reload screenshots: it still shows
the landing animation and a different zoom. The creation-time oracle reports
paused, but that does not prove the subsequently captured UI remained paused.
Consequently the save-creation launch is **not** the episode starting screen;
future episodes must load the archived save and establish their own readiness.
The four reload screenshots, unlike the creation screenshot, show `Paused`.

The old oracle read `Tile.rotation`, which did not provide building orientation.
The new setup mod reads `Tile.build.rotation` where a building exists. Sixteen
linked tiles provide non-null rotation; this is not sixteen distinct buildings.
There is no rotated conveyor control yet, so direction-sensitive scoring is not
validated by this core-only initial world.

The implementation uses the pinned release's setup save/load APIs described in
[SaveIO.java](https://github.com/Anuken/Mindustry/blob/v160.2/core/src/mindustry/io/SaveIO.java).
Building rotation belongs to the building, as shown by
[Tile.java](https://github.com/Anuken/Mindustry/blob/v160.2/core/src/mindustry/world/Tile.java)
and [BuildingComp.java](https://github.com/Anuken/Mindustry/blob/v160.2/core/src/mindustry/entities/comp/BuildingComp.java).
These APIs are setup and oracle access only; no controller has played this study.

## Reproduce

Use the extracted assets/environment in [REPRODUCE.md](REPRODUCE.md), Linux, and
a new output directory. To reproduce this scenario, use v2 and the pinned save;
v1 creates another potentially different Fork world.

```sh
python3 research/benchmark_discovery/mindustry_reset_v2.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --save research/benchmark_discovery/results/mindustry-reset-01/canonical.msav \
  --out /home/taka/mindustry-reset-rerun
python3 research/benchmark_discovery/audit_mindustry_reset.py \
  /home/taka/mindustry-reset-rerun \
  --reference research/benchmark_discovery/results/mindustry-reset-01/create/oracle.json
```

The audit checks source hashes, copied save identity, screenshot hashes, process
cleanup, projection shape and exact projection equality. It does not run under
`python -O` (assertions must remain enabled). The manifest records the JAR hash;
the audit does not re-download or authenticate assets. Existing ancillary Java
security/HTTPS initialization and audio errors remain in raw logs; no system
Java repair or new installation-time claim is made.

## Next task gate

Before a task-level pilot, establish a live player/camera/input-ready state after
reload, then define a small resource-flow construction task with ordinary pointer,
rotation, held input and pause/resume. Record player/unit state, core inventories,
and controlled simulation phase separately. Calibrate the independent task score
against missing, reversed, partial and collateral placement states and actual
resource delivery. The current projection omits units, player pose, timers,
building inventories other than core copper, and RNG state. It cannot establish
whole-engine or resumed-trajectory determinism. CPU/GPU overhead was not compared
in this follow-up, and no human-speed, token-cost, or architecture promotion claim
is supported.
