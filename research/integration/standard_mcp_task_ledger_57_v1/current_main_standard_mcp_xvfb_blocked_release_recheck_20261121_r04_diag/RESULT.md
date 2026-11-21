# Standard-caller Xvfb XRes budget diagnostic R04

Status: `DIAGNOSTIC_ONLY_NOT_A_PRODUCT_PASS`.

One optimized-mode run changed `_XRES_DISCONNECT_TIMEOUT_S` in memory from 0.15 s to 1.0 s; no repository source was modified for the run. XRes returned `disconnected` after about 199.5 ms, and the independent release worker verified A/B up. The old A obligation remained held during the fixture's one-second withheld cancel acknowledgement, and the event trace records repeated A KeyPress/KeyRelease effects: count 1 before cancellation and 20 at the horizon. The independent old-task oracle failed. The scheduled delayed B KeyPress was not observed. The fresh-session task oracle passed, the old generation stayed UNKNOWN/no-replay, and final keys were up.

This supports that the 150 ms bound can expire before the observed XRes response. It also shows the longer acknowledgement hold allows repeated effects while A remains held; it does not show that the scheduled delayed B event executed. The diagnostic is not evidence for changing a production bound by itself.
