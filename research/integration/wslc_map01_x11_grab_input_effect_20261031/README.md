# MAP01 game response to X11 input during a server grab

This WSLc experiment evaluates a possible response to #9899's check-to-input race. It does not modify or invoke the agent-interface runtime. A private Xvfb server hosts Freedoom2 MAP01 in ASYNC_SPECTATOR at 35 tics/s. An X11 client sends an `f` key down, waits 85 ms, and sends key up; it queries server key state after each event. In the grab condition, the same client confirms an X server grab before key down and confirms ungrab only after key up. In the normal condition it performs the same pair without a grab. The game-engine ammo is sampled before, immediately after, and for 15 subsequent samples about 50 ms apart; it is evaluation-only.

| Run | Condition | Server key state | Later ammo |
| --- | --- | --- | --- |
| z01 | no grab | down, then up | 50 → 49 |
| z02 | grab | down, then up | 50 → 50 |
| z03 | grab | down, then up | 50 → 50 |
| z04 | no grab | down, then up | 50 → 49 |

In this fixed-order, small test, a confirmed X11 down/up during the grab did not produce observed ammunition consumption, unlike the two ungrabbed controls. The test does not independently prove exactly how the game processed queued events or that this holds for other applications or durations. Server-side key release and game-side effect are different observations. A server grab can delay other X clients, including the game; prior isolated testing also showed that killing a grab owner while a button is held can leave that button down until an external release. Thus this result is a reason not to adopt a naive long server grab as a complete fix; it neither excludes other scoped designs nor proves their correctness.

Each run used a fresh WSLc container, private Xvfb, skill 1, seed 991031, one CPU, 1 GiB, no network, pinned image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25, and a 20 s external process timeout. Fixed order was normal/grab/grab/normal. Main was 3217466fe70d011b5ee74cfa9915ccc20a9d84db. ZIPs preserve exact scripts, conditions, Xvfb logs, telemetry and exit codes. `python audit.py` checks event order, key states, sampling and controls. No model, overlay, input guard, crash test or MAP01 completion claim is involved in this series.
