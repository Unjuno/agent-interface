# Procedural Operations Facility v0

A very small native 2.5D FPS-style benchmark environment for Agent Interface research.

The facility is not intended to measure human-like game skill. It is an **agent-native operations environment** that combines continuous navigation with terminal work and concurrent monitoring. The benchmark is designed so that perception, state tracking, local control and multiple independent obligations can continue while a rich model is waiting.

This v0 is a construction/screening environment. It is not yet evidence that any Agent Interface candidate improves general computer control.

## World

The executable contains a deterministic software raycaster and a procedural facility episode. There is no external game engine or network dependency.

A seeded episode contains:

- an FPS-like facility with rooms/corridors, WASD movement and relative mouselook;
- a **SOURCE terminal** showing an alphanumeric value;
- a **DEST terminal** with an editable field and submit effect;
- an **ASSEMBLY terminal** with solid pieces and matching spatial slots;
- configurable decoy terminals;
- up to **12 independent watcher channels** that pre-warn, become authoritative, and must be acknowledged before their deadlines while the main work continues.

The visible task surface does not print per-step instructions such as “go here”, “type this”, “click this”, or internal stage names. Task semantics are expressed through world state, terminal visuals, code data, spatial affordances and watcher state.

## Why the concurrency matters

The environment intentionally allows the following to overlap:

```text
navigation / mouselook
+ source/destination terminal work
+ assembly work
+ F1..F12 watcher obligations
+ independent world time
```

Human performance is not the ceiling. `watcher_count`, event rate and deadlines can be increased beyond comfortable human serial attention to test agent-native parallel perception/state tracking and local control.

## Determinism and seeds

All episode generation and watcher schedules derive from a 64-bit seed.

The committed regression allocation is:

```text
seeds/regression.txt
```

The same seed + difficulty vector generates the same episode specification hash and the same deterministic fixed-step mechanics.

The hidden construction oracle uses privileged state only to verify reachability/mechanics. It calls the same movement, keyboard, pointer and text action functions as an external controller, but **its result is not an agent-performance score**.

## Difficulty vector

`--difficulty [0,1]` is only a convenient preset. Scientific evaluation should sweep individual axes with repeated `--set KEY=VALUE` overrides.

Current axes:

- `watcher_count` — concurrent monitoring channels, 0..12;
- `event_rate_hz` — aggregate watcher event rate;
- `watcher_prewarn_ticks` — anticipation/inhibition interval;
- `watcher_deadline_ticks` — active acknowledgement deadline;
- `watcher_events_each` — obligations per watcher;
- `code_length` — SOURCE→DEST transcription length;
- `assembly_pieces` — number of spatial pieces;
- `assembly_tolerance_px` — placement precision;
- `decoy_terminals` — irrelevant but visually similar workstations;
- `fov_deg` — navigation/perception field of view;
- `terminal_visual_scale` — projected terminal size;
- `world_deadline_ticks` — global task deadline;
- `strict_inhibition` — whether premature watcher acknowledgement fails closed.

Example:

```bash
./build/facility --oracle-run \
  --seed 30303 \
  --difficulty 0.4 \
  --set watcher_count=10 \
  --set event_rate_hz=5 \
  --set watcher_deadline_ticks=30 \
  --set assembly_tolerance_px=7
```

## Build and test locally

Requirements are only a C11 compiler, libc/libm and Python 3 for the test harness.

```bash
make clean test
./run_regression.sh
```

`make test` performs:

- C core negative/positive controls;
- seed-deterministic spec checks;
- 12 fixed regression seeds across difficulty 0.0 / 0.5 / 1.0;
- deterministic rendered-frame checks;
- public/private information-boundary checks;
- one-axis override isolation;
- invalid-parameter fail-closed checks;
- seeded mechanics/render performance smoke;
- paired-harness same-seed identity checks.

## Container

The Dockerfile builds and runs the complete fixed-seed construction test suite **during image build**. The runtime image contains the native world plus Python paired harness.

```bash
docker build -t procedural-operations-facility-v0 .
docker run --rm procedural-operations-facility-v0 \
  --oracle-run --seed 10101 --difficulty 0.5
```

The benchmark container is intended to remain private to the evaluator. An evaluated controller should be a separate process/container and receive only rendered frames plus the allowed keyboard/mouse/text action channel.

## Controller protocol

`--stdio` exposes a low-level world process for the evaluator harness. Its public state is intentionally minimal:

```json
{"schema":"procedural-operations-facility-public-v0","tick":0,"done":false}
```

Supported evaluator-mediated action commands are:

```text
KD W / KU W
MOUSE <relative-dx>
KD E
KD F1 ... KD F12
PD <x> <y>
PM <x> <y>
PU <x> <y>
TEXT <text>
STEP <ticks>
```

`SNAP` and private `REPORT` exist on the evaluator side. `paired_harness.py` does not pass those capabilities through to controllers.

The controller receives a rendered PPM frame and `{tick, done}` only. It never receives the seed, specification hash, hidden code, terminal coordinates, watcher schedule or scorer state.

## Paired fixed-seed harness

The harness runs two independent controller sessions against identical seeded episodes and counterbalances arm order.

```bash
python3 paired_harness.py \
  --seeds seeds/regression.txt \
  --difficulty 0.5 \
  --left  'python3 controllers/noop_controller.py' \
  --right 'python3 controllers/noop_controller.py' \
  --output /tmp/facility-pairs
```

The included no-op controller is only a protocol test. Replace the two commands with a genuine Plain controller and Agent Interface candidate for an actual performance comparison.

For formal evaluation, use fresh hidden seeds generated **after candidate freeze**. Keep the committed fixed seeds for deterministic regression/debugging only.

## Performance modes

Environment/mechanics throughput can be measured without a model:

```bash
./build/facility --bench --seed 424242 --episodes 500 --difficulty 0.6
```

This reports oracle mechanics episodes/s and software-render frames/s. Those are **instrument performance**, not agent capability.

Actual agent performance should be measured by `paired_harness.py` or a hardened successor using the same hidden seed and difficulty vector for B0/C1, recording correctness first and failure frontiers per axis.

## Current limits

- 2.5D raycast world rather than full polygonal 3D;
- no X11/desktop compatibility layer in v0; formal observations are framebuffer PPMs mediated by the harness;
- terminal UI is intentionally small and synthetic;
- watcher tiles are abstract monitoring channels rather than full independent camera feeds;
- local paired harness is a protocol/reproducibility tool, not a hardened anti-cheat boundary because controllers on the same host can potentially inspect processes/files;
- no rich-model/image/token/cache accounting yet;
- no held-out generator-family service yet;
- no real-app transfer claim.

The next promotion step is not more oracle solving. It is to connect a genuine Plain visual controller and one Agent Interface candidate to identical hidden seeded allocations and sweep one difficulty axis at a time.
