# Mindustry visual self-use: resume, move, pause

One assistant-controlled development episode used the unchanged `session_v9`
backend and `executor_v3`, the same pointer candidate previously used in the
OpenTTD pilot. It loaded the pinned save, resumed with Space, inspected a later
image for the spawned unit, held `d` for a declared 800 ms, and paused with Space.
The final image shows the unit east of its starting core and the `Paused` label.
The independent engine sample stream was inspected only after control closed.

**Finding: the pinned initial save is not immediately player-ready.** Its initial
sample has `player_dead=true` and `unit=null`. Resuming permits a beta unit to
spawn; the first post-resume image does not yet show it. An additional observation
shows the unit at the core. A task harness must establish unit/input readiness,
not infer it from save equality or a completed resume command.

## Evidence

[Raw episode](results/mindustry-readiness-01/manifest.json),
[audit](results/mindustry-readiness-01/audit.json),
[independent samples](results/mindustry-readiness-01/readiness.jsonl).

- Three accepted/completed programs, no rejected programs, 12 exact observations.
  The audit decodes all 12 AIT packets and compares their reconstructed pixels
  to each referenced PNG, including reused images.
- 858 read-only engine samples, initially paused/no unit, subsequently live with
  one unit ID, finally paused with that unit alive. The final unit is 202.158 world
  units east and 0.160 north of its first live sample. This is movement evidence,
  not precision targeting or calibrated movement gain. Core copper remains 200.
- Every terminal verifies no held keys/buttons; process cleanup and unchanged
  canonical save are recorded. Individual physical key-up timestamps are absent.
- Original-resolution visual review: `001.png` paused/no unit; `003.png` resumed
  but no visible unit; `005.png` unit at core; `011.png` unit east and paused.

| Program | Admission → first capture | Admission → first emitted observation | Admission → terminal |
|---|---:|---:|---:|
| resume | 92.173 ms | 144.144 ms | 472.800 ms |
| inspect-spawn | 51.951 ms | 300.663 ms | 323.761 ms |
| move-right-pause | 91.005 ms | 339.377 ms | 1,942.534 ms |

These are same-process Python runtime timestamps. The first resume capture reuses
the paused image, so it is **not** the first useful evidence of resumed state.
Emission is not model receipt. The Java samples have sequence indices and game
ticks, not a verified common clock; do not subtract them from Python timestamps.
Initial capture to final program terminal is 71.837 seconds. Between programs,
terminal-to-next-admission gaps are 18.368 and 25.295 seconds. The actual episode
therefore does not demonstrate human-like tempo despite short local operations.
Actual model tokens, cost and model receipt timestamps remain missing.

The 800 ms requested hold took 1,245.866 ms as a whole step, including observation
work. The 100 ms Space steps took 347.899 and 571.532 ms. These are not measured
physical key-down durations; the log cannot establish exact hold overshoot.
The existing owner enforces program lease expiry separately, but that is not a
measurement of per-step input duration. Do not compensate movement by these
numbers or promote a timing improvement without a controlled comparison.

## Scope and reproduction

`mindustry_interactive_v1.py` adds private game setup and a final diagnostic archive;
it does not modify the shared backend. This deliberately reuses the OpenTTD
candidate and does not integrate the newer runtime31/socket16/checkpoint stack.
The declared task is readiness only. Movement-direction sanity checks in the
offline audit are post-hoc, not a preregistered construction or gameplay score.
No pointer construction, resource flow, multi-object planning, recovery or
held-out task has been evaluated here.

From Linux with the existing assets, use a new output directory:

```sh
python3 -u research/benchmark_discovery/mindustry_interactive_v1.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out /home/taka/mindustry-readiness-rerun
```

The CLI emits an initial image and accepts the existing bounded stdin protocol:
`clock`, `submit` (fresh ID, observed sequence, runtime lease deadline, steps),
`cancel`, and `finish`. Observe actual images and make new decisions; archived
nanosecond deadlines must not be replayed. `finish` closes input and archives the
read-only diagnostic samples. The fixed-cohort audit runs with:

```sh
python3 research/benchmark_discovery/audit_mindustry_readiness.py
```

Source hashes cover the explicitly listed inputs; this is not a full environment
lockfile. Ancillary Java security/audio diagnostics remain in the game logs.
The setup observer samples approximately every 100 ms on the game update trigger;
its overhead is not isolated. Source references for
[Space pause binding](https://github.com/Anuken/Mindustry/blob/v160.2/core/src/mindustry/input/Binding.java)
and [update triggers](https://github.com/Anuken/Mindustry/blob/v160.2/core/src/mindustry/core/Logic.java)
were checked against the pinned release.

Next: create a controlled player-ready starting point, then calibrate a small
resource-flow task against missing/reversed/partial/extra placement and actual
delivery. Compare candidate input/observation timing under the same workload,
with independent key transition timestamps and retained semantic correctness.
