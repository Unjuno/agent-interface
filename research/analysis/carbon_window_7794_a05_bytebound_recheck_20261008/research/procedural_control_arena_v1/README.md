# Procedural Control Arena v1

> **Status:** construction benchmark environment. This is a fast screening/regression apparatus, not yet a formal shared benchmark and not a substitute for real desktop/game/domain evidence.

v1 is a deliberately small real-time GUI world for Agent Interface research. It keeps the renderer and mechanics cheap while composing ordinary computer-input primitives into one procedural episode. The controller-facing surface is intended to remain ordinary pixels plus keyboard/pointer/text input; hidden episode truth stays on the evaluator side for scoring and replay.

## Why v1 exists

v0 established a tiny procedural arena for movement, moving-target selection, WAIT→SWITCH freshness, and typing. v1 keeps that core and adds the missing interaction classes discussed for the benchmark design:

- simultaneous keyboard + pointer control;
- drag/drop precision;
- multi-piece spatial assembly;
- continuous pointer tracing/drawing;
- controlled interruption and recovery;
- independent per-axis difficulty overrides.

The goal is not to reward game-specific skill. The goal is to expose **where correctness breaks** as visual, motor, temporal, precision, and sequence demands increase.

## Full-suite primitives

One `full` episode contains every primitive exactly once in seed-randomized order:

1. `MOVE` — hold/release WASD to enter a goal region.
2. `TARGET` — identify and click a specified moving shape among distractors.
3. `WAIT -> SWITCH` — abstain, then reject the prepared/stale target and act on the newly authoritative target.
4. `TYPE` — focus a terminal, type a generated code, press Enter.
5. `COMBO` — hold a required keyboard key while clicking the correct moving target.
6. `DRAG` — pick up one piece and place it into its socket within tolerance.
7. `ASSEMBLY` — place multiple pieces into matching ghost slots.
8. `TRACE` — drag through an ordered path from START to END within tolerance.
9. `RECOVERY` — execute a correct target action, observe a forced visible interruption/relocation, reacquire, and complete the action again.

`--suite core` retains only `MOVE / TARGET / SWITCH / TYPE` for cheaper regressions.

## Difficulty model

`--difficulty` remains a convenience scalar in `[0,1]`, but v1 is explicitly designed for **individual-axis sweeps**. Every mapped field is present in the episode report and can be overridden independently with repeated `--set KEY=VALUE` arguments.

Current axes include:

- `target_radius`
- `target_speed`
- `distractor_count`
- `visual_similarity`
- `move_zone_radius`
- `move_deadline`
- `target_deadline`
- `switch_wait`
- `switch_deadline`
- `typing_length`
- `typing_deadline`
- `objective_sample_radius`
- `drag_radius`
- `drag_tolerance`
- `drag_deadline`
- `assembly_pieces`
- `assembly_tolerance`
- `assembly_deadline`
- `combo_deadline`
- `trace_tolerance`
- `trace_checkpoints`
- `trace_deadline`
- `recovery_deadline`
- `recovery_displacement`

Example one-axis study:

```bash
python3 arena.py --difficulty 0.35 --set target_speed=150 --set distractor_count=4
```

Formal analysis should report failure frontiers per axis rather than treating the aggregate scalar as a scientific score.

## Run

The engine uses Python's standard library. The GUI uses `tkinter`.

```bash
cd research/procedural_control_arena_v1
python3 -m unittest -v test_engine.py
python3 arena.py --suite full --difficulty 0.35 --report /tmp/arena-v1-report.json
```

For deterministic mechanics/debugging:

```bash
python3 arena.py --seed 123 --clock fixed --suite full --difficulty 0.5
```

For real-time inference-gap/reaction work:

```bash
python3 arena.py --clock realtime --suite full --difficulty 0.5
```

## Presentation contract

The evaluated surface separates **desired state** from **motor policy**.

- moving-object tasks show a visual sample of the desired color/shape, not prose such as “click the blue circle”;
- the SWITCH task changes the visual sample and readiness lamp from pending to active without naming WAIT/SWITCH/stale state;
- COMBO shows a keycap constraint plus the visual target sample, but does not narrate the action sequence;
- TYPE shows the code as task data and a terminal field, but does not say “click/type/Enter”;
- DRAG and ASSEMBLY use solid pieces plus matching ghost geometry;
- TRACE uses a path, checkpoints and endpoint glyphs instead of procedural text;
- RECOVERY is expressed by the target actually moving after the first valid effect, with no “interrupted/reacquire” coaching;
- stage names, stage counts, exact remaining deadlines, PASS/FAIL labels, failure reason and fingerprint are not rendered to the evaluated controller.

The generic benchmark interface may declare that ordinary keyboard, pointer and text input are available. Per-episode presentation should specify the objective/constraint, not the physical recipe for satisfying it. Natural-language instruction following can be added later as an explicit independent axis rather than being baked into every primitive.

## Controller-visible boundary

The GUI does not display:

- seed;
- object IDs;
- correct target IDs;
- future stage payloads/order;
- scorer internals;
- generator state.

At run completion the evaluator report contains the seed and exact episode specification for replay. The source tree itself is **not a hardened secrecy boundary**: formal held-out evaluation still needs a separate evaluator/container/VM arrangement so the controller cannot inspect source, process arguments, memory, or private reports.

## Scoring and diagnosis

Correctness is fail-closed for consequential errors. Typed failure reasons/loci include:

- `deadline_miss` → `REALTIME_DEADLINE`
- `motor_miss`, `drag_drop_miss`, `assembly_drop_miss`, `trace_deviation`, `missing_chord` → `MOTOR`
- `wrong_target`, `premature_action` → `CONTROLLER_DECISION`
- `stale_action` → `STALE_STATE`
- `typing_error` → `TYPING`

Reports also retain stage durations, ordinary input event counts, recovery events/successes, full event ledger, process CPU time, and peak RSS where available.

The arena intentionally does not collapse these into one leaderboard score.

## Current non-goals / remaining gaps

v1 still does **not** establish general Agent Interface capability. In particular:

- it is 2D, not true 3D modeling/manipulation;
- `ASSEMBLY` and `TRACE` are precision/spatial-control proxies, not Blender-equivalent tasks;
- explicit Agent Interface `YIELD` remains an external orchestration outcome rather than a fake keyboard game action;
- model/token/image/cache accounting belongs in the external paired harness;
- held-out generator-family rotation and candidate-freeze commit/reveal are not implemented here;
- formal Plain-vs-candidate paired results have not been run;
- cross-domain transfer remains required before interpreting an arena gain as general improvement.

## Intended benchmark use

Use v1 to answer questions such as:

- At what target speed does a candidate begin to miss real-time deadlines?
- Does a local controller reduce latency without increasing wrong-target or stale-action failures?
- Does faster control preserve drag/assembly/trace precision?
- Does a mechanism help continuous control but hurt typing or spatial construction?
- After an interruption, how quickly and reliably does control reacquire the task?

A useful result is an interpretable **correctness-preserving failure frontier**, not merely a higher game score.
