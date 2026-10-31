# MAP01 short X11 server grab around key down

This WSLc series follows #9900. Three modes send the same `f` key down, wait at least 85 ms, then send key up. `normal` uses no server grab. `grab` holds the X11 server grab until after key up. `short` confirms the grab, sends and confirms key down, ungrabs while the key is still down, waits, then sends and confirms key up. The same X11 client queries the server keymap for down and up. The game-engine ammo is evaluator-only and sampled before, immediately after and for 15 later samples. This experiment uses direct XTEST; it does not run the agent-interface guard or combine a visual check with input.

| Run | Mode | Server key state | Grab duration | Later ammo |
| --- | --- | --- | ---: | --- |
| aa01 | normal | down → up | — | 50 → 49 |
| aa02 | grab | down → up | 85.732 ms | 50 → 50 |
| aa03 | short | down; still down after ungrab; up | 1.123 ms | 50 → 49 |
| aa04 | short | down; still down after ungrab; up | 0.575 ms | 50 → 49 |
| aa05 | grab | down → up | 86.731 ms | 50 → 50 |
| aa06 | normal | down → up | — | 50 → 49 |

In this small fixed-seed series the short grab allowed the observed ammunition decrease that the long-grab runs did not show. The game-side event processing mechanism is not established, and this is not an atomic check-and-press implementation or a general latency/reliability result. The short mode deliberately leaves the key down after releasing the server grab: a crash in that interval can leave input held. Prior isolated tests documented that hazard, and this series did not test crash recovery or concurrent target changes. The `finally` block attempts emergency release on ordinary exceptions, but cannot itself cover process death or a blocked server. No recommendation to deploy this mode follows from this sample.

Six fresh private Xvfb WSLc containers used Freedoom2 MAP01 ASYNC_SPECTATOR 35 tics/s, skill 1, seed 991031, one CPU, 1 GiB, no network, image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25, and a 20-second external timeout. Fixed order was normal/grab/short/short/grab/normal; main was 68ddab8e5dabac574a6bf56cbef28512dad84026. ZIPs retain all scripts, logs, timings, samples, conditions and exit codes. `python audit.py` checks mode-specific event ordering, input-state observations and controls. No model, overlay, cancellation or MAP01 completion is tested.
