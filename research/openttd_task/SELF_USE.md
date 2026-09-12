# First OpenTTD shared-pointer self-use — 2026-09-13

Follow-up: [guarded placement](GUARDED_PLACEMENT.md) replayed these coordinates and
detected one extra surrounding road that this original score did not constrain.
A separate corrected visual episode passed the expanded score. The original
single-episode result below retains its original, narrower interpretation.

One assistant-controlled visual episode passed the existing independent three-tile
road contract. This is evidence that the shared pointer candidate can perform a
small dense-GUI/placement task. It is not formal benchmark adoption, human-speed
parity, broad planning competence, or a comparison against the previous runtime.

`interactive_v1.py` loads the byte-pinned `results/cohort-03/baseline.sav` in a fresh
Linux/Xvfb/Openbox process and private profile. It installs only the observer
GameScript. After setup focus, all task inputs go through `session_v9.Backend` and
`executor_v3.Executor`; there are no engine building calls or adapter input
shortcuts. The controller selected coordinates from screenshots. Engine tile
records were used only for setup readiness and final independent scoring, not
action selection. The assistant already had the task/setup design in context;
this was not a blind or held-out test.

Three submitted programs opened the road toolbar, selected its direction and
positioned the pointer, then dragged from A toward C. Final scoring, after a new
post-control observer sample, verified:

- target tiles 678, 679, 680 are roads owned by company 0;
- both adjacent connections work in both directions;
- forbidden tiles 742, 743, 744 remain road-free.

The score covers these six tiles and two edges only. It does not prohibit or
measure additional construction outside that region, full-world changes, cost,
route optimality, or long-horizon planning. Stronger minimal-edit/placement
contracts need an independently scored surrounding region before such claims.

## Measured record

Artifacts: `results/self-use-01/`. Offline `audit_self_use.py` verifies pinned
sources/save, all 15 AIT-to-PNG exact reconstructions, three successful program
terminals with verified release, initial-negative/final-positive engine score,
and process/save cleanup. Extra transitive dependency hashes are recorded at
audit time, explicitly separate from the initial launch manifest.

| Quantity | Observed value |
|---|---:|
| Submitted programs | 3 |
| Pointer steps | 4 (two clicks, one move, one drag) |
| Archived exact observations | 15 |
| Open-toolbar program, accepted to terminal | 1472.7 ms |
| Select-direction/move program | 623.2 ms |
| Drag/observe program | 653.1 ms |
| Initial capture to last program terminal | 63.51 s |

The last number includes assistant reasoning, tools and host delivery. These
intervals are not model inference latency or an estimate of human performance.
The run used full records and screenshots; actual model token/cost usage was not
measured. The private game/WM/X server all exited and canonical save bytes stayed
unchanged.

## Architecture feedback

The first program requested 100 ms of full-frame pixel quiet with a 1200 ms
timeout. It sampled nine frames and timed out after 1222.8 ms. Animated water and
other game changes remained visible. This demonstrates that full-frame quiet
was unavailable during this sample; it does not isolate which animation caused
each changed pixel. Program completion correctly stayed separate from semantic
task completion. Subsequent decisions used observed GUI state without another
quiet wait.

Coverage therefore now includes a small real OpenTTD toolbar/placement episode
alongside DOOM motor stress. The next shared design question is task-relevant
feedback, stale-action handling and bounded pointer continuation across domains,
not optimizing a single game's score. Repeated fresh episodes and richer GUI
tasks remain necessary. Mindustry's fixed-state feasibility gate remains next in
the domain portfolio; Luanti stays a future 3D candidate.

Reproduce a fresh interactive episode from repository root in the prepared WSL environment:

```sh
python3 research/openttd_task/interactive_v1.py \
  --root /home/taka/agent-interface-bench-feasibility \
  --out research/openttd_task/results-local/new-self-use
```

The stdin JSON protocol supports `clock`, `submit`, `cancel`, `finish`; submits
require the latest observation sequence and an absolute runtime-clock lease
within 30 seconds. `finish` performs the independent score and shuts down owned
processes. Re-run archived evidence checks with:

```sh
python3 research/openttd_task/audit_self_use.py research/openttd_task/results/self-use-01
```
