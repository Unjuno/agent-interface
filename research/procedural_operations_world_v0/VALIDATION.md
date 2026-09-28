# Local construction validation — validity-hardened v0.2 — 2026-09-28

Scope: benchmark substrate mechanics, anti-shortcut controls, paired-episode invariants, deterministic rendering, X11 integration smoke, and instrument overhead. This is **not** Agent Interface performance evidence.

Environment: current ChatGPT Linux execution container, x86-64, GCC, X11/Xvfb. Docker/Podman CLI is not installed in this execution container.

## Build

Built with:

```text
-O2 -std=c11 -Wall -Wextra -Wpedantic
```

Final build: **0 compiler warnings**.

## Construction / validity regression suite

`./test_ops_world`: **17/17 PASS**.

The suite covers:

1. independent difficulty overrides and cross-parameter feasibility rejection;
2. deterministic `(seed, family_key, config)` generation/replay;
3. task-subset/dependency-graph, presentation-family, map-opening, station-layout variation;
4. unique target visual semantics at 64 moving objects;
5. exact precomputed alert schedules and total-event-rate semantics independent of burst size;
6. future alert schedule invariance under different ACK timing;
7. 64 watcher + 64 object + 16-way simultaneous-burst generation;
8. recoverable terminal bad-submit followed by successful correction;
9. recoverable assembly miss/reset followed by successful completion;
10. alert ACK, hard missed-deadline, and inactive false-ACK controls;
11. hard wrong-target control plus bounded recoverable motor miss and recovery-budget exhaustion;
12. precomputed target relocation independent of action timing;
13. one-second realtime catch-up equivalence to 120 internal fixed substeps;
14. 200-alert event-ledger stress without silent truncation;
15. framebuffer equality when hidden `alerts_acked` / `target_hits` scorer-progress counters differ;
16. render/cursor operation across multiple presentation families;
17. exact reset plus stable `episode_hash` replay.

## Independent seed/family audit

A separate 10,000-seed audit at 64 moving objects produced:

```text
semantic_collisions=0/10000
generation_failures=0/10000
presentation_mask=0xfff   # all 12 presentation families observed
map_mask=0xff             # all 8 map transforms observed
```

A boundary-like valid alert configuration (`watchers=64`, `required_alerts=32`, `event_rate=1/s`, `alert_deadline=2s`, `burst=8`, `episode=50s`) generated a complete feasible schedule for **10,000/10,000 seeds**:

```text
unsolvable_generated=0/10000
last scheduled alert range=27.126..37.536 s
```

## Paired-episode invariant

Alert arrivals are absolute precomputed episode events. ACK actions never schedule the next alert. The regression suite runs the same episode with different ACK timing and verifies:

- identical immutable alert schedule;
- identical episode hash;
- identical future schedule cursor at equal simulation time;
- no ACK-dependent `next_event` mutation.

The first target relocation coordinate is also generated before execution and is identical regardless of first-hit time.

These controls specifically prevent B0 and C1 from receiving different future test questions solely because one controller reacted earlier.

## Hidden scorer UI control

Two otherwise identical worlds were rendered with different hidden values for:

- cumulative alert ACK count;
- target-hit count.

With visible world state held equal, the 640×360 framebuffers were byte-identical. Numeric benchmark quota/progress is therefore not rendered by the v0.2 task cue layer.

## X11 / headless smoke

`run_smoke.sh` passes:

- native rebuild;
- 17/17 tests;
- headless software framebuffer + evaluator JSON report;
- 64-object/64-watcher render stress lane;
- real X11 executable under Xvfb for a bounded run.

## Instrument cost after validity hardening

Stress configuration:

```text
watcher_count=64
required_alerts=0
event_rate=0
object_count=64
assembly_pieces=12
episode_seconds=3600
640x360 full software render
```

10,000 fixed simulation+render frames:

```text
10,000 / 10,000 frames
1.067481 s
9,367.85 frames/s
0.1067 ms/frame
max RSS 2,072 KiB
native binary 68,936 bytes
```

100,000 deterministic in-process resets under the same 64-object/64-watcher capacity:

```text
1.353003 s
73,909.67 resets/s
13.530 us/reset
```

The additional task/schedule/presentation generation increases reset cost compared with the prior hardened build, but the instrument remains orders of magnitude below a 60/120 Hz frame budget on this host.

These are local diagnostic measurements, not portable benchmark claims.

## Current decision

**VALIDITY-HARDENED CONSTRUCTION PASS / FORMAL BENCHMARK HOLD.**

The concrete shortcut and fairness defects found in the two local audits are repaired. Formal performance claims still require:

1. secure framebuffer/HID mediation and evaluator-private seed/family/report channel;
2. automatic paired B0/C1 execution against one frozen generated episode;
3. fresh hidden allocation after candidate freeze;
4. true held-out generator/presentation implementation rather than only private nonce variation of public code;
5. repeated parameter-frontier sweeps with uncertainty reporting;
6. external model/image/token/cache/resource accounting;
7. independent real-application/domain transfer.
