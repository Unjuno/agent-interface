# Procedural Control Arena v0

A deliberately small, dependency-light interactive benchmark prototype for Agent Interface research.

The arena is **not a game-skill benchmark**. It is an experimental apparatus for asking where a computer-control interface stops preserving correctness as visual, motor, temporal, and sequencing demands increase.

## Scope

One episode composes four primitives in a seed-randomized order:

- `MOVE`: hold/release `WASD` to enter a visual goal zone;
- `TARGET`: identify a visually specified moving shape and click it;
- `WAIT -> SWITCH`: abstain during a wait interval, then reject the prepared/stale target and act on a newly authoritative target;
- `TYPE`: click a terminal, type a seed-generated code, and press Enter.

The visible controller surface is only the ordinary window: pixels plus keyboard and pointer input. The GUI does not reveal the seed, object IDs, correct target IDs, future stages, or scorer state.

This v0 is intentionally narrower than the repository's cross-domain promotion contract in Issue #12. It is a fast screening/regression fixture, not evidence of general Agent Interface performance and not a replacement for desktop, DOOM, OpenTTD, Mindustry, Luanti, or held-out cross-domain evaluation.

## Continuous difficulty

`--difficulty` accepts a real value in `[0,1]` and monotonically changes declared axes:

| Axis | 0.0 -> 1.0 |
| --- | --- |
| target radius | 34 px -> 10 px |
| target speed | 0 -> 165 px/s |
| distractors | 2 -> 10 |
| movement goal radius | 70 px -> 24 px |
| movement deadline | 10 s -> 4 s |
| pointer deadline | 8 s -> 2.6 s |
| WAIT interval | 2.4 s -> 0.65 s |
| SWITCH deadline | 6 s -> 2.2 s |
| typing length | 3 -> 10 chars |
| typing deadline | 10 s -> 4 s |

The benchmark should be analyzed as a set of failure frontiers, not collapsed immediately into one scalar score.

## Run

The only GUI dependency is Python `tkinter`; the state engine and tests use the standard library only.

```bash
cd research/procedural_control_arena_v0
python3 -m unittest -v test_engine.py
python3 arena.py --difficulty 0.35 --report /tmp/arena-report.json
```

For a headless X11 smoke in a container/CI host with Xvfb:

```bash
xvfb-run -a python3 arena.py --difficulty 0.25 --clock fixed --report /tmp/arena-report.json
```

The interactive process intentionally does not auto-solve. Use the unit-test oracle helper only as a positive control for generator/scorer mechanics.

## Seed and replay contract

When `--seed` is omitted, the runner creates a fresh 63-bit seed and does not place it in the window. At episode termination the JSON report contains the seed and full `EpisodeSpec`, making the exact generated task replayable:

```bash
python3 arena.py --seed <reported-seed> --difficulty <reported-level>
```

For paired comparison, the harness should generate a seed out of band, launch baseline and candidate in isolated agent sessions against the same seed, and keep that seed unavailable to both controllers until the run is over.

**This source tree by itself is not a hardened secrecy boundary.** If the evaluated agent can inspect benchmark source, process arguments, or benchmark memory, it can specialize to the generator. Formal held-out use therefore requires a separate evaluator/container/VM boundary and fresh or held-out generator composition as specified by the benchmark protocol.

## Clock modes

- `realtime`: environment progress follows monotonic wall time. Use this for inference-gap/reaction evaluation.
- `fixed`: one 1/60 s simulation step per GUI tick. Use this for deterministic mechanics/debugging, not for wall-time performance claims.

Reports retain simulation time and monotonic wall offsets separately.

## Scoring and diagnostics

The engine is fail-closed on consequential errors and records typed failure reasons including:

- `deadline_miss`
- `motor_miss`
- `wrong_target`
- `premature_action`
- `stale_action`
- `typing_error`

The event ledger records stage transitions and ordinary input events. A successful episode requires all composed stages to complete with no forbidden action.

## v0 limitations

- 2D only; no 3D spatial construction or drawing task yet.
- No drag-and-drop primitive yet.
- No rich-model/token accounting inside the arena; that belongs to the external paired harness.
- No cryptographic commit/reveal service yet.
- No hidden generator-family rotation yet; seed secrecy prevents exact-episode memorization but does not prevent distribution-level specialization.
- No formal baseline/candidate result is claimed by landing this prototype.

The next validation step is to establish that controlled parameter sweeps produce interpretable failure frontiers for a plain computer-control baseline and at least one Agent Interface candidate while holding model/task/evaluator conditions fixed.
