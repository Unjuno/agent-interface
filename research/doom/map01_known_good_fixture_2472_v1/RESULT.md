# ViZDoom known-good fixture reproduction — #2472

## H/T/D/C/U

**Hypothesis.** The earlier direct-action HOLDs were fixture-specific; reproducing the repository's stated known-good setup might expose a measurable rotation effect.

**Test.** Pinned container `python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`; `vizdoom==1.2.3`; private Xvfb; `freedoom2.wad`, `MAP01`, `Mode.PLAYER`, RGB24; buttons `MOVE_FORWARD, USE, TURN_LEFT, TURN_RIGHT`; one `[0,0,1,0]` TURN_LEFT action for 4 tics.

**Data.** `before_angle=0.0`, `after_angle=0.0`, `angle_delta=0.0`, `reward=0.0`. `before_screen_sha256=68a6aaab3f24098f4e0ad2b67cdd285af3533d41c4ddc5c06593fcf0daddcd6f`; `after_screen_sha256=68a6aaab3f24098f4e0ad2b67cdd285af3533d41c4ddc5c06593fcf0daddcd6f`. Cleanup completed.

**Conclusion.** `HOLD_NO_MEASURABLE_TURN`. The specified direct-action fixture did not reproduce a measurable turn in this pinned current run. This does not authorize transport, controller, target-admission, general effect-detection, or end-to-end utility claims.

**Unknowns.** Why the repository's historical known-good setup differs from this current reproduction; no retries or fixture changes were performed in this run.

**Scope.** No model, X11 input transport, user desktop, or task-success claim. The result preserves the failure exactly and is not a modification of earlier results.
