# Standard-caller Xvfb XRes budget diagnostic R04

Status: `DIAGNOSTIC_ONLY_NOT_A_PRODUCT_PASS`.

One optimized-mode run changed `_XRES_DISCONNECT_TIMEOUT_S` in memory from 0.15 s to 1.0 s; no repository source was modified for the run. XRes returned `disconnected` after about 199.5 ms, and the independent release worker verified A/B up. The original delayed action then produced repeated effects: count 1 before cancellation and 20 at the horizon, so its independent task oracle failed. The fresh-session task oracle passed, the old generation stayed UNKNOWN/no-replay, and final keys were up.

This supports that the 150 ms bound can expire before the observed XRes response and that extending it does not cancel already accepted delayed server work. The diagnostic is not evidence for changing a production bound by itself.
