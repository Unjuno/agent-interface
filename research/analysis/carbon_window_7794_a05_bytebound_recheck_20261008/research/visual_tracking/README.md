# Moving-screen visual feedback development study

Follow-up: [asynchronous execution and latest-observation delivery](ASYNC_INTEGRATION.md)
are now connected and exercised by the assistant. The frozen study below remains unchanged.

The [event-retention follow-up](EVENT_RETENTION.md) preserves detected warnings
and target loss across latest-image changes, with six fresh functional probes
and one assistant-operated trial. It uses fixture-specific pixel detectors.

This experiment adds a wall-clock-driven X11 target-tracking task. The red
target keeps moving while the controller waits. A green player responds to OS
Left/Right keys. The controller locates both from RGB screenshots; application
state is opened for scoring only after control ends.

It tests a necessary component of continuous control: how much tracking quality
is lost when the same simple motor policy updates its held input less often.
It does not implement model inference overlap, generic perception or DOOM.

## Fresh frozen screen

The [protocol](PROTOCOL.md) and source hashes were saved before starting
`results/fresh-r1`. Twelve six-second episodes completed, with verified input
release, across three seeds, two cadences and two arms. Both arms capture at
nominal 50 ms intervals; only input-decision cadence differs. Local updates at
each capture. Delayed updates every 250 or 1000 ms using a fresh image, then
holds the input. This simulates decision cadence, not inference pipeline latency.

| Paired condition | Delayed mean error | Local mean error | Delayed time within 30 px | Local time within 30 px |
|---|---:|---:|---:|---:|
| 250 ms cadence, 3 seeds | 39.52 px | 20.04 px | 45.71% | 90.00% |
| 1000 ms cadence, 3 seeds | 242.31 px | 20.26 px | 11.55% | 90.19% |

Each episode's metrics are time-weighted from actual application timestamps;
the table averages the three episodes per arm. Every paired error difference
favored local feedback in this screen. This is not a broad significance claim.
The analysis recomputes error from logged target/player positions, checks
duration and controller counts, and verifies frozen source hashes. See
`results/fresh-r1/analysis.json` for each pair and `summary.json` for all episodes.
The target is one seeded sine trajectory family with known colors, no occlusion,
no distractors and no changing goal. Conclusions do not generalize beyond this
task without further experiments.

## Actual assistant invocation

In `results/assistant-01`, the assistant viewed the start image and submitted
`{"method":"local"}` through `live.py` (the full command is retained). That
bounded six-second method completed with mean error 26.36 px, 88.74% of time
within 30 px, 123 local decisions and verified release. The assistant chose a
prewritten method; it did not make 123 model decisions or visually inspect each
frame. No model API calls or token measurement run inside the method. The
`delay_ms` field is inactive in local mode. The current invocation interface
waits for completion; it does not stream feedback back to the planner.

## Failures and provenance

The first development attempt timed out waiting for the initial window before
task input. Its source snapshots, empty control trace and diagnostic screenshot
are retained under `development-local-01`. That screenshot comes from a separate
diagnostic run, not from the failed episode. The captured exception is recorded
in `failure.json`. An unchanged-code retry (`development-local-02`) completed.
The cause is unconfirmed. Before the fresh freeze, setup added a wait for the
public `_NET_SUPPORTING_WM_CHECK` property; no causal fix claim is made.

All tasks used fresh private Xvfb/Openbox sessions under Ubuntu/WSL and Python
Xlib. Sampled screenshots (approximately one per second) illustrate execution;
full images are not archived for every control tick. Controller positions and
timings and the separate application oracle are retained. No exact transport,
token-compression or human-speed claim is made by this study. A failure closes
the private server, but this runner is not a production cancellation/watchdog
implementation. The previous asynchronous executor remains a separate track.

## Reproduce and continue

```sh
python3 analyze.py results/fresh-r1
python3 batch.py --out ../../results-local/tracking-new
python3 live.py --out ../../results-local/tracking-live --seed 860901 --mode local
```

Use unused output paths. `live.py` pauses at its ready event so an agent can
inspect `initial.png` and submit `{"method":"local"}` or `{"method":"delayed"}`.
The batch currently fixes the protocol's seed set; a new independent cohort
requires a new protocol/runner revision, preserving this one.

Next: connect this kind of bounded visual motor method to the asynchronous
executor, expose useful feedback while it runs, and evaluate observation age,
goal changes and target loss during planner delay. Then move to a more varied
dynamic environment and the separately defined DOOM milestone. Do not optimize
this simple arena indefinitely or substitute its score for the actual goal.
