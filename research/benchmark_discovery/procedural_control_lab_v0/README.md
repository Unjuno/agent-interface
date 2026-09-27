# Procedural Control Lab v0

> **Status:** construction benchmark prototype. This is not yet a formal shared benchmark and does not replace the real-application/domain suite.

A tiny real-time GUI environment for measuring computer-control behavior while keeping the game itself cheap enough for rapid iteration. The controller-facing contract is intentionally ordinary: pixels plus keyboard/mouse input. Exact episode truth remains on the benchmark side for independent scoring.

## What v0 measures

One generated episode composes four stages:

1. `WAIT` — input before `GO` is a forbidden effect.
2. `MOVE` — use ordinary WASD/arrow key-down/key-up control to enter a goal region.
3. `CLICK` — click a moving target among moving distractors before a deadline.
4. `TYPE` — click a terminal, type the displayed code, and press Enter.

This gives a single lightweight world that can expose recognition/grounding, keyboard hold/release, pointer targeting, typing, inhibition/NO-OP behavior, multi-step continuation, and real-time deadline failures. It does **not** yet claim drag/drawing/3D construction coverage.

## Difficulty

`--difficulty` is continuous in `[0,1]`. The current mapping changes multiple declared axes:

- target size decreases;
- target speed increases;
- distractor count increases;
- click/typing deadline tightens;
- movement goal shrinks;
- player movement slows slightly;
- required wait grows;
- typing string length grows;
- instruction font shrinks.

The raw mapped values are always included in the public result so a future study can sweep one axis at a time instead of treating the scalar as a scientific score. Formal experiments should prefer explicit matched parameter sweeps and failure frontiers.

## Run locally

The implementation uses Python's standard library only.

```bash
python3 benchmark.py --difficulty 0.35 --mode gui \
  --result /tmp/control-lab-result.json \
  --private-log /tmp/control-lab-private.json
```

For deterministic development/replay, pass a seed explicitly:

```bash
python3 benchmark.py --seed 123 --reveal-seed --difficulty 0.5 --mode gui
```

For construction tests only, an oracle positive-control driver is available:

```bash
python3 benchmark.py --seed 123 --difficulty 0.5 --mode headless-perfect
python3 -m unittest -v test_benchmark.py
```

The positive-control route is benchmark construction machinery and must never be exposed to an evaluated controller.

## Xvfb / container smoke

```bash
xvfb-run -a python3 benchmark.py --seed 123 --difficulty 0.5 --mode gui --smoke-ms 300
```

A minimal Dockerfile is included. The intended evaluation image contains only Python, Tk/X11, Xvfb, this game, and benchmark logging. Agent Interface itself should remain outside the image so the benchmark image can be frozen independently.

## Visibility boundary

Public output contains `run_id`, mapped difficulty, stage/result and aggregate metrics. By default it does **not** emit the seed, target actor id, typing oracle, event trace, or generator state. Those can be written to a separately protected `--private-log` for scoring/replay.

Containerization helps make that boundary enforceable, but this prototype alone does not prove anti-leak isolation. A formal evaluator still needs an execution boundary where the agent cannot inspect the benchmark process, filesystem, private log, generator, or seed.

## Current metrics

The result records correctness-relevant violations plus:

- early actions during WAIT;
- wrong/missed clicks;
- typing errors;
- key events and pointer clicks;
- total action count;
- stage completion times;
- first movement latency;
- click reaction time;
- click error distance.

Correctness is a hard condition: completing the final stage after a forbidden action does not count as success.

## Non-claims / next gates

v0 is a construction artifact. Before formal benchmark use, at least the following remain:

- paired Plain-vs-candidate runner with isolated model sessions;
- one-axis and factorial difficulty sweeps rather than a single composite level;
- fresh/held-out seeds and held-out mechanic compositions;
- stronger process/filesystem leak controls;
- drag/assembly and explicit ambiguous/YIELD mechanics;
- timing-clock validation under real model latency;
- negative scorer controls for every failure class;
- repeated reset/replay tests and resource measurements;
- matched transfer checks against real desktop apps and existing DOOM/Mindustry/OpenTTD/Luanti coverage.

The benchmark should be used to locate failure frontiers and diagnose mechanisms, not as a single leaderboard score.
