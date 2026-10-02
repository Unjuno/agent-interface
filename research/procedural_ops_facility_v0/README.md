# Procedural Operations Facility v0

A native, ultra-light 2.5D operations-facility benchmark substrate for Agent Interface research.

This is intentionally not a human-parity FPS benchmark. The world combines FPS-style continuous navigation with concurrent visual monitors and computer-use-like terminal/assembly work so difficulty can extend beyond what a single human operator can comfortably monitor serially.

## Integrated episode

A seeded episode contains one continuous environment:

- procedural maze-like facility navigation using WASD + view rotation;
- multiple independent watcher tiles that can become active while navigation continues;
- a moving-target camera feed with distractors and stale-target switches;
- a destination terminal with a generated code-transfer task;
- a precision assembly board;
- a forced relocation after the first placement to exercise recovery/reacquisition.

The watcher and tracking processes continue as independent world processes rather than being represented as a list of prose instructions. The native engine scores world effects and typed failure reasons.

## Fixed-seed automation versus formal evaluation

`--auto-reference` is a **construction/reference controller**. It is deterministic and may use private world state. It exists to test reachability, replay, input mechanics, rendering, container execution, and benchmark overhead without a human operator. It must not be reported as Agent Interface performance.

Example deterministic construction run:

```bash
./facility --headless --auto-reference --seed 424242 --difficulty 0.45 --report /tmp/report.json
```

Formal B0/Candidate evaluation should instead freeze both controller configurations, generate fresh hidden seeds out of band, pair the exact same episodes across isolated controller sessions, and expose only the rendered surface plus ordinary input.

## Parameterized difficulty

`--difficulty [0,1]` is only a convenience preset. Individual axes are independently overrideable using repeated `--set KEY=VALUE` arguments.

Current axes:

- `map_size`
- `maze_loops`
- `watcher_count`
- `watcher_event_rate_hz`
- `watcher_deadline_ticks`
- `track_distractors`
- `track_speed_px_per_tick`
- `track_target_radius_px`
- `track_event_interval_ticks`
- `track_deadline_ticks`
- `code_length`
- `assembly_pieces`
- `assembly_tolerance_px`
- `recovery_displacement_px`
- `episode_deadline_ticks`
- `fov_deg`

Example:

```bash
./facility --headless --auto-reference --seed 424242 --difficulty 0.4 \
  --set watcher_count=8 \
  --set watcher_event_rate_hz=1.7 \
  --set track_speed_px_per_tick=3.0 \
  --set assembly_tolerance_px=9
```

Formal results should be per-axis failure frontiers, not one aggregate difficulty score.

## Build and test

Native dependencies are intentionally small: C11, libm and X11. Headless simulation/rendering does not require a running X server; the GUI smoke uses Xvfb.

```bash
make
./run_tests.sh
```

Container:

```bash
docker build -t procedural-ops-facility-v0 .
docker run --rm --entrypoint /facility/run_tests_container.sh procedural-ops-facility-v0
```

## Modes

- `--headless --auto-reference`: deterministic construction/replay run.
- `--gui --auto-reference --no-sleep`: X11/Xvfb end-to-end render/input-mechanics smoke without manual operation.
- `--benchmark N`: N fixed-seed reference episodes, reporting mechanics throughput.
- `--render-benchmark N`: CPU software-render throughput and frame hash.
- `--snapshot FILE.ppm`: deterministic framebuffer artifact.

## Scope limits

v0 establishes the lightweight facility substrate and automated fixed-seed test path. It does not yet provide the hardened external framebuffer/HID server for formal B0/Candidate isolation, held-out generator families, rich-model accounting, or cross-domain transfer evidence. Those are promotion gates, not assumptions.
