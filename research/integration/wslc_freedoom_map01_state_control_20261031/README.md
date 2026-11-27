# WSLc Freedoom MAP01: input release and observed position

A two-arm exploratory control uses the current-main guarded X11 bridge with a private Xvfb and the ViZDoom Freedoom2 MAP01 game, monsters not disabled, skill 1, seed 991031. Both fresh allocations use the same image, script and IWAD hash, a 35 Hz asynchronous spectator game and one CPU; the container has no network. d05 waits without input for two seconds; d06 holds W for two seconds through the guarded keyboard program and releases it. Both sample game-provided position, health and kill count before and after the interval, then for approximately four seconds. No model is called and the game telemetry is not supplied to a controller.

| Run | Interval displacement | Post-interval displacement | Health / kill change |
| --- | ---: | ---: | ---: |
| d05 no input | 0 | 0 | 0 / 0 |
| d06 W held | 538.031 | 87.076 | 0 / 0 |

The W program has two key emissions and a verified empty release receipt before the post-action sample; W was also up on final X11 readback and owner close verified release. Despite that, the game-reported position continued to change during the subsequent samples. This observation does not identify the cause or establish an exact stopping time; it shows that neutral input readback alone is not evidence of an immediately stationary game state. Position values are game-engine telemetry, not an independent physical sensor. The no-input arm has no release attempt, because no input was dispatched.

There was no observed health loss or kill in either short run. Monsters were not disabled, but no evidence here establishes enemy exposure, threat detection, successful combat, model-latency coverage, finite live recovery, an exit, or MAP01 completion. Fixed order, two separate games and startup/sampling timing also limit causal interpretation. The task result stays null.

Failures are retained: d01 exited 139 after ViZDoom could not write under the read-only working directory; d03 caught a wait-only keyboard validation error before task input. The runner catches its own errors and therefore d03's container exit 0 is not a success signal. d02 and d04 were prepared but never run. d05/d06 are the new pair after correcting these setup issues. Raw inputs, logs, X11 receipts, initial screenshots and telemetry samples are in the archives; `python audit.py` checks all six allocations, image associations, receipt states, timing order and recomputed displacement. No run was replayed.
