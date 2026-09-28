# Procedural Operations World v0.2

A tiny, CPU-only 2.5D operations world for Agent Interface screening and failure-frontier research.

The FPS-like shell is only the substrate: it supplies continuous navigation, viewpoint control, occlusion, moving world state, concurrent events, and real-time deadlines. The work itself is closer to computer-use/operations tasks: visual data transfer, terminal entry, precision assembly, target tracking/reacquisition, and asynchronous alert handling while other work continues.

The world is written in C with a software raycaster and primitive software UI. Its only window-system dependency is X11. It does not require a GPU API, browser engine, physics engine, audio, network, or external art assets.

## Status

**VALIDITY-HARDENED CONSTRUCTION PASS / FORMAL BENCHMARK HOLD.**

v0.2 fixes concrete benchmark-shortcut and paired-evaluation defects found in two adversarial audits. It is suitable as a fast experimental substrate. It is not yet sufficient for a general Agent Interface performance claim because the secure evaluator/controller boundary, automatic B0/C1 harness, true held-out generator implementation, and cross-domain transfer study remain external work.

## Design contract

The benchmark should measure computer-control capability rather than skill at one scripted game.

- CPU-only and extremely lightweight so instrument overhead does not dominate the measured controller.
- Real-time world state continues while a workstation panel is open or a rich model is waiting.
- Difficulty is a **parameter vector**, not one scientific difficulty score.
- Tasks are generated as varying subsets/dependency graphs rather than one fixed action script.
- Exogenous events are generated before execution and do not change when the controller acts faster or slower.
- Controller-visible evidence is rendered state plus ordinary keyboard/pointer/text input.
- Hidden scorer counts, seed, schedule, generator nonce, and evaluator diagnostics remain report-side.
- Consequential harmful actions fail closed; bounded recoverable mistakes are measured separately.
- Presentation/layout varies by episode so a fixed pixel-coordinate macro is not the intended solution.
- Agent-native concurrency can exceed human-comfortable concurrency (up to 64 moving objects and 64 watcher channels in v0.2).

## Generated episode

Each episode deterministically freezes, from `(seed, private family key, difficulty vector)`:

- map transform plus seed/family-dependent opened passages;
- player start and view angle;
- selected work-task subset;
- work-task dependency graph;
- station positions, colors, and icon family;
- moving-object initial state and one semantically unique target;
- target relocation coordinate used after the first valid target effect;
- source transfer code;
- assembly piece semantics/start/slot geometry;
- complete asynchronous alert schedule with absolute simulation times and channel IDs;
- presentation family, including watcher layout/permutation and alert palette.

The resulting `episode_hash` is retained by the evaluator. The same seed/family/config therefore produces the same exogenous test schedule even if two controllers react at different times.

### Task graph

The three work primitives are:

- visual transfer: read the source station and make the terminal state match;
- assembly: place solid pieces in matching ghost geometry;
- moving target: identify the visual sample, produce one valid effect, then reacquire it after relocation.

`work_task_count` selects 1–3 of these per episode. `dependency_depth` controls whether selected work tasks are parallel or chained. Alert monitoring is independently enabled by `required_alerts > 0` and remains concurrent with the work graph.

Locked/completed stations are visually de-emphasized. The world does not show per-step motor instructions or hidden task/scorer names.

## Concurrent alert model

Alerts are **precomputed exogenous events**. ACK timing never schedules the next alert.

`event_rate` means total alert arrivals per simulated second. `alert_burst` controls how many of those arrivals are simultaneous; increasing burst size does not multiply the nominal total arrival rate.

For valid configurations the generator creates exactly `required_alerts` scheduled arrivals within the episode budget. It rejects configurations whose rate/deadline/channel capacity cannot guarantee a feasible schedule.

Watcher presentation is not one permanent top strip. Episode presentation families distribute/permutate watcher channels among top rows, side banks, four-corner banks, or top/bottom banks, and vary the active-alert palette. An acknowledged channel returns to its normal visual state after a short feedback flash; cumulative ACK count is not rendered.

## Recoverable vs forbidden actions

Some mistakes are realistically recoverable and are measured instead of immediately ending the episode:

- empty/motor miss;
- incorrect terminal submission;
- assembly drop outside tolerance.

These increment `recoverable_errors`. A subsequent valid effect records a recovery. `recovery_budget` controls how many recoverable mistakes are allowed before `recovery_exhausted` becomes a hard failure.

Actions that would make a benchmark easy to brute-force remain hard failures:

- inactive watcher acknowledgement;
- wrong moving object;
- missed alert deadline;
- evaluator/instrument event-ledger overflow.

Thus limited correction is measurable without reopening blind-click or exhaustive-search shortcuts.

## Difficulty vector

All important load dimensions are independently configurable with repeated `--set key=value`.

| Parameter | Meaning |
| --- | --- |
| `target_speed` | moving-object speed |
| `object_radius` | apparent object size |
| `object_count` | simultaneously moving objects (1–64) |
| `watcher_count` | asynchronous watcher channels (0–64) |
| `event_rate` | **total** alert arrivals / simulated second |
| `alert_deadline` | acknowledgement deadline |
| `alert_burst` | simultaneous arrivals per opportunity |
| `required_alerts` | exact scheduled alerts required |
| `typing_length` | source/terminal transfer-code length |
| `assembly_pieces` | assembly pieces |
| `assembly_tolerance` | placement tolerance in pixels |
| `navigation_speed` | avatar translation speed |
| `mouse_gain` | viewpoint sensitivity |
| `episode_seconds` | episode wall/simulation budget |
| `work_task_count` | generated work primitives, 1–3 |
| `dependency_depth` | work graph depth, 0–2 |
| `recovery_budget` | recoverable mistakes before hard failure |

Formal studies should sweep one causal axis at a time and then preregister selected interactions. Do not use one aggregate difficulty number as the primary result.

Example concurrency stress:

```bash
./ops_world --seed 42 --family-key 99173 \
  --set watcher_count=64 \
  --set required_alerts=64 \
  --set event_rate=20 \
  --set alert_deadline=2 \
  --set alert_burst=16 \
  --set object_count=64
```

## Generic input contract

Ordinary controls only:

- `W/A/S/D` key down/up — navigation;
- mouse motion — viewpoint control in world mode;
- left mouse button — world/UI interaction;
- right mouse button or `Esc` — leave a panel;
- alphanumeric keys / Backspace / Enter — terminal input.

The per-episode framebuffer does not say “click X”, “press W”, expose stage names, display benchmark PASS/FAIL reasons, or render hidden score quotas such as `alerts_acked / required_alerts` or target-hit counts.

## Build and run

```bash
sudo apt-get install build-essential libx11-dev xvfb xauth
make clean all
./test_ops_world
```

Interactive/Xvfb lane:

```bash
./ops_world --seed 42 --family-key 99173 --fixed --report /tmp/report.json
```

Headless deterministic render:

```bash
./ops_world --seed 42 --family-key 99173 \
  --headless-frames 120 --dump-ppm /tmp/frame.ppm --report /tmp/report.json
```

Instrument render benchmark with alert obligations disabled:

```bash
./ops_world --seed 42 --family-key 99173 --bench-frames 10000 \
  --set watcher_count=64 --set required_alerts=0 --set event_rate=0 \
  --set object_count=64 --set assembly_pieces=12 --set episode_seconds=3600
```

Long-lived reset benchmark:

```bash
./ops_world --seed 42 --family-key 99173 --bench-resets 100000 \
  --set watcher_count=64 --set required_alerts=0 --set event_rate=0 \
  --set object_count=64 --set assembly_pieces=12
```

## Public vs evaluator-private boundary

The intended formal public channel is only:

- framebuffer observations;
- ordinary HID-like keyboard/pointer/text events.

Evaluator-private material includes:

- seed;
- `family_key`;
- task graph and dependency masks;
- absolute alert schedule;
- target relocation coordinate;
- scorer state/failure locus;
- evaluator report and event ledger.

The JSON report reveals these after the run for replay/audit.

`family_key` is a private generation/presentation nonce, **not a cryptographic isolation mechanism**. Passing it on a command line is construction/debug functionality only. Formal evaluation still needs a separate evaluator process/container/VM so the controller cannot inspect command-line arguments, process memory, report files, source, or the X server outside the framebuffer/HID mediation layer.

## Anti-specialization position

v0.2 materially increases variation through task graphs, map openings, station placement/colors/icon families, watcher placement/permutation/palette, object state, assembly layouts, and a private family nonce.

That does **not** make the public generator a true held-out benchmark family. A general capability claim still requires evaluator-private or post-freeze held-out generator/presentation families and independent real-application transfer evaluation.

## Evaluator report

After execution the report contains:

- seed and private family key;
- `episode_hash`;
- complete difficulty vector;
- generation/task/presentation metadata;
- full exogenous alert schedule and target relocation;
- required world effects;
- recovery/error counters;
- input counters;
- simulation/wall timing;
- event ledger.

This makes exact episode reconstruction and post-run paired-audit possible without exposing those fields to the controller during execution.

## Remaining formal HOLD gates

1. secure framebuffer/HID broker and evaluator-private process boundary;
2. automatic B0/C1 paired harness using the same frozen `episode_hash`;
3. fresh hidden allocation after candidate/runtime freeze;
4. true held-out generator/presentation implementation beyond the public generator algorithm;
5. repeated parameter-frontier allocation and uncertainty reporting;
6. external model/image/token/cache/CPU/RAM accounting;
7. independent real-application/domain transfer evidence.

The next step should be the paired evaluator/harness, not richer graphics.
