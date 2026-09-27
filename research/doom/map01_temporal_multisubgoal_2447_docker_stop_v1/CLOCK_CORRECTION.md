# Clock-probe correction — 2026-09-27

This file supersedes the live-clock conclusion in the initial Docker first-rung report, while preserving that report and its original observations unchanged.

## What was wrong

The first probe initialized a ViZDoom game and then only slept. In this headless environment that left the game at its initial pause tic. The project’s current known-good MAP01 launcher does not measure that state: it starts the exact private X11 session, initializes the game as visible ASYNC_SPECTATOR at 35 tics/s, finds and focuses the Doom window, calls `advance_action(1, True)` once to leave the startup pause, records the starting tic, waits two seconds without engine advances, then calls `advance_action(1, True)` once to sample the ending tic. I omitted both startup unpause and the supported GUI session/focus path in the earlier checks. Therefore those checks do not show a clock defect and the prior STOP must not be interpreted as an Issue #2447 experiment STOP.

## Corrected construction probe

Re-ran one bounded no-controller-input clock probe in the pinned local Docker image, using the current-main `gui_suite.Session` (Xvfb 1280x800x24, Openbox, private Xauthority/XDG state), exact v12 MAP01 mode/config/button/game-variable settings, and the project’s focus/clock-sampling sequence.

- Image ID: `sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`
- Mode/map/skill/ticrate: ASYNC_SPECTATOR / MAP01 / 1 / 35
- Seed: 2447002 (construction-only; not an Issue allocation)
- IWAD: wheel-bundled `freedoom2.wad`, 28,787,748 bytes, SHA-256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`
- Focused window: `VIZDOOM 1.3.0 (ZDOOM 2.8.1+)`
- Pre-wait sample after one startup advance: tic 16
- Passive wait: 2.0289 seconds
- Engine advances during wait: 0
- Post-wait sample after one ending advance: tic 87
- Observed tic delta: +71; threshold >=35 passed.

The shortfall between 70 expected and 71 observed tics is compatible with the timing of the before/after sampler; the probe is a clock-readiness gate only, not a performance measurement.

## Updated status

The Docker/X11 asynchronous clock prerequisite now passes for the bundled construction fixture. This is not the Issue #2447 sequence experiment and does not establish multi-subgoal safety, gate efficacy, or transfer. The exact #2447 formal schedule and fault controls still require a fresh immutable preregistration before running. The previous report’s no-formal-rows and no-retries accounting remains true; only its interpretation of the bare-sleep probes is corrected.

The original STOP report remains intact as provenance. Do not cite its bare-sleep outcomes as evidence of an engine/live-clock limitation.
