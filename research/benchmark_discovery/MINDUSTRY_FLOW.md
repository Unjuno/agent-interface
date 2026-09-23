# Mindustry resource-flow score calibration

Six fresh Linux/X11 GUI runs now calibrate a narrow construction contract against
actual engine transport. A fixed copper item source at (137,51) feeds six eastward
conveyors at x=138..143, y=51 into the existing core. The contract requires all six
placements/directions, preservation of the other tiles in a 112-tile guard region,
and at least one additional copper in the core after at least 600 game ticks.

**The extra-placement case transports copper but fails the contract.** Resource
delivery alone is insufficient evidence of correct construction. This is the
Mindustry counterpart to the earlier OpenTTD surrounding-placement guard.

| Engine-authored state | Copper delivered | Placement / guard finding | Contract |
|---|---:|---|---|
| Complete | 32 | Six eastward conveyors, guard unchanged | verified |
| Missing middle tile | 0 | (140,51) absent | contradicted |
| Reversed middle tile | 0 | (140,51) faces west | contradicted |
| Partial | 0 | Last three conveyors absent | contradicted |
| Complete plus extra | 31 | Extra conveyor at (140,50) | contradicted |
| Empty | 0 | All six conveyors absent | contradicted |

These are calibration results from fixture-authored engine states, **not agent
construction achievements**. No controller received oracle data or chose game
actions. The sampler reports `task_success=null`; Python evaluates the explicit
narrow contract after the application exits. The case name is used by setup and
the audit's expected-results table, never by the score function.

## Evidence and checks

- [Frozen plan](mindustry_flow_plan_v1.json) specifies the cases, guard, required
  state, source, minimum duration and copper increase before execution.
- [Manifest](results/mindustry-flow-01/manifest.json) records source/JAR hashes and
  the plan. Each case archives before, constructed and after projections, a final
  PNG, raw stdout/stderr and process cleanup.
- [Audit](results/mindustry-flow-01/audit.json) replays all six cases through
  [the score](mindustry_flow_score_v1.py), verifies measured source and screenshot
  hashes, and checks readiness and cleanup. All owned processes exited; none of
  the six application exits required SIGKILL after SIGTERM.
- Six offline malformed/open controls (missing tile, duplicate tile, unpaused
  window, insufficient elapsed ticks, boolean copper, claimed oracle authority)
  produce UNKNOWN, with `contract_satisfied=null`.

The score implementation was written after inspecting the first complete-case
result. This is development calibration, not a held-out test or preregistered
implementation comparison. The exact source/contract revision and raw results
remain available for a later fixed comparison. The constructed snapshots are
diagnostics; the score consumes only before/after and the plan.

The [official ItemSource implementation](https://github.com/Anuken/Mindustry/blob/v160.2/core/src/mindustry/world/blocks/sandbox/ItemSource.java)
supports configured copper output and engine-driven transport. The source is a
sandbox fixture component. The scorer does not simulate conveyor throughput or
grant success from placement counts alone. Positive delivery is observed from
core inventory delta; it does not establish causality against every alternative
source of copper in a future agent-controlled task.

## Reproduction

Use the environment/assets from [REPRODUCE.md](REPRODUCE.md). A new output path is
mandatory. Each case uses a fresh profile, Xvfb/Openbox and application process.
The pinned save is checked before use and copied into the private profile.

```sh
python3 research/benchmark_discovery/mindustry_flow_v1.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/mindustry-flow-rerun
python3 research/benchmark_discovery/audit_mindustry_flow_v1.py
```

The audit targets the archived `results/mindustry-flow-01` cohort. For another
cohort, feed its before/after JSON and manifest plan to `mindustry_flow_score_v1.score`;
do not overwrite the original evidence. Assertions require ordinary Python, not
`python -O`. No new environment installation or asset download is required.

## Boundaries and next pilot

Simulation ends on the first completed update beyond 600 ticks. Observed windows
are 600.609–601.763 ticks, not identical deterministic trajectories. Single-case
delivery counts and approximately 17-second setup-plus-simulation durations are
not throughput comparisons, resource-overhead measurements, or human-speed data.
Software GL and the known ancillary Java security/audio diagnostics are retained.

The guard compares block, team, direction, floor and overlay for 112 tiles; it
does not cover the entire world, all inventories, build cost, temporary damage,
or an extra tile built and later removed. Core location and source item are
checked, but this is not a full causal/anti-cheating verifier. A future task must
account for construction resource costs and separate post-construction delivery
from manual resource acquisition. Input-window authority is not derived from
the game being paused; the latter only describes this calibration's sample phase.

Next, create an empty-route, player-ready fixture and use ordinary shared pointer
input to build the route from observed images. Keep engine-authored calibration
distinct from that self-use episode. Verify direction, prohibited placements and
actual delivery after control, then add fresh configurations before adoption.
