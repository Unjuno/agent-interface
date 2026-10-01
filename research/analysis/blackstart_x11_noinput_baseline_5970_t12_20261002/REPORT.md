# Issue #5970 T12 — no-input baseline

## Disposition

`PASS_EMPTY_NO_INPUT_BASELINE` for the 500 ms private-Xvfb control. With the exact T3-derived app focused, the T10 parent-only observer and X RECORD were armed; neither recorded any key event. `a` and `Shift_L` were neutral both before and after. The candidate did not import XTEST or dispatch input. Independent audit reported zero RECORD rows and zero observer rows.

This rules out a key event spontaneously appearing during the measured startup baseline only. It does not explain the extra KeyRelease that appears during input trials or establish any production, deployed #4135, recovery, or task-benefit claim. Docker Desktop remained unavailable; private WSL2 Xvfb was used.
