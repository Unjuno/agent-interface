# X11 cancellation, release, and delayed MAP01 ammunition effect

This WSLc live experiment extends #9891 and #9889. A private Xvfb display hosts Freedoom2 MAP01 in ASYNC_SPECTATOR at 35 tics/s, skill 1, seed 991031. The guarded X11 bridge starts an attack with a 500 ms wait; a separate X11 client observes that `f` is held, waits 50 ms, then requests cancellation. The bridge interrupts the wait, attempts key release, and returns a receipt; game ammo is evaluator-only, not supplied to the controller. The control waits 50 ms without input. Every run uses a fresh network-none WSLc container, pinned image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25, one CPU, 1 GiB memory. The mounted Python runtime was checked against main 6a9c787d2caf9740612de65bd2539846dd87cad4 in #9891; intervening 93b9efbea19350477e2a9c6d69ab6349612011f7 adds only research evidence.

| Run | Condition | Receipt | First sample after release/action | Later sample |
| --- | --- | --- | --- | --- |
| r09 | no input | withheld | ammo 50 | 50 |
| r10 | held attack, cancel | interrupted wait; verified empty release; effect unknown | ammo 50, tic 31 | 49, tic 34 |
| r11 | held attack, cancel | interrupted wait; verified empty release; effect unknown | ammo 50, tic 31 | 49, tic 34 |
| r12 | no input | withheld | ammo 50 | 50 |

For both cancellations, the monitor observed the key held, then requested cancellation, and the returned release timestamp preceded the sample at 50; a later sample reported 49. The first sample showing 49 was about 107 ms after the release timestamp in both runs; this is observation latency, not the actual effect time or a general upper bound. The already emitted input can cause game effects after cancellation and after an immediate post-release sample. This does not establish a hit or kill, exact causal timing, a general recovery delay, model performance, MAP01 completion, or correctness in other environments. The receipt retains `failed_op_effect` as unknown and replay is not authorized by these findings.

All twelve allocations are preserved. In r01/r04 the no-input control completed; r02/r03 refused the cancellation scope before dispatch because the query worker was not enabled. r05–r08 stopped before dispatch because query-worker mode requires process identity. The corrected identical runner produced r09–r12 in fixed order withhold/cancel/cancel/withhold. Container exit alone is not a success indicator: inspect result status and receipts. `python audit.py` verifies the retained outcomes, monitor and release ordering, samples, and invalid attempts. No model was called and no product code changed.
