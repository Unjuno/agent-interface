# Shared DOOM self-use: observed presentation gap

**Correction:** [later byte/image audit](FEEDBACK_PILOT.md) confirms the saved
002.png contains the normal scene and matches its published Git bytes. The
black appearance described below was the assistant-received presentation, not
a proven black saved PNG or engine-rendering failure. The failed task remains.

`shared-assistant-01` is actual assistant operation of frozen `session_v6.py`,
seed 990201. The assistant viewed initial PNG 001, saw the target left of center,
requested a 150 ms Left hold, then viewed PNG 002. That image was almost black,
with only the HUD face visible. A separate read-only observation returned the
same pixels. The assistant stopped rather than treating a terminal completion
as successful gameplay. The episode remained unfinished, player alive, tic 1741.
This is one unsuccessful task, not a successful DOOM demonstration.

The frame/source auditor passes all five frames and two program releases.
Owner shutdown is verified. These checks prove retained-image transport and
cleanup, not a useful rendered scene or successful delivery into game behavior.
The artifact failure is retained; no core/runtime change is promoted.

## Timing and interpretation

Initial capture to first input admission was 20,936.740 ms. This includes tools,
image inspection, model reasoning, clock request and scheduling; it is not a
model-only latency. Accepted program to first local image-ready was 120.695 ms
for the hold and 53.001 ms for refresh. Neither proves time to useful feedback:
the observation was black and the client/model receipt time is uninstrumented.
There is no same-model comparison, token saving or human-speed claim.

## Exploratory gap comparison

`gap_probe.py` declares two fresh instances of the same seed 990202 with zero
or twenty seconds between initial observation and input. Both use ordinary
100 ms Right hold followed by a separate observation through the unchanged
adapter. Source/case/clock manifests are saved before the runs. This is a
single ordered exploratory pair, with different launch transport from the
interactive PTY run; it does not isolate every possible cause.

Both runs pass the existing input readiness checks, with four exact frames each
and observed clocks 34.974 / 35.010 tic/s. **Black output was not reproduced.**
A post-hoc fixed world crop (321,181)-(961,580), excluding HUD, has exactly the
same pixels before/after the hold within both runs, and 99.767% nonblack pixels.
This flags absence of visible turn feedback in the retained interval. It cannot
distinguish missing game input, stale rendering, or insufficient observation
coverage. The `readiness_pass` values intentionally retain the original narrow
checks; they must not be relabeled as game-input correctness.

`analyze_gap.py` audits frames/source hashes, records the crop diagnostic and
interaction timing, and labels the scripted audit scope correctly. Cropping is
offline analysis, not a modified controller observation or a semantic oracle.

## Next experiment

Instrument input-to-game response and render freshness separately: retain normal
ASYNC_SPECTATOR speed, test a longer visible turn with delayed X11 observations,
and compare post-control orientation/engine state only after controller actions.
Inspect how engine rendering behaves while the client is idle; any environment
refresh candidate needs a separate revision and a no-speed-change clock check.
Compare PTY versus pipe launch if the black-screen difference persists. Do not
silently add engine action selection or hide this issue with compressed output.

Official [mode documentation](https://vizdoom.farama.org/main/api/python/enums/)
states that asynchronous play progresses without waiting for agent actions.
[Rendering documentation](https://vizdoom.farama.org/main/api/python/doom_game/)
describes render-all-frames for visible previews; neither establishes that this
specific integration stays visually fresh across planner gaps. Root cause remains
unproven. Shared DOOM task correctness and Research Freeze qualification stay open.

## Response diagnostic update

[Four response probes](RESPONSE_DIAGNOSTIC.md) establish successful OS-key shooting
through the shared backend in one scripted trial, while Right-key rotation stays
unresolved. Extra engine refresh and delta-button availability did not fix it.
The 43 frames and release/close records audit; no candidate is promoted.

## Follow-up resolution of directional input

[BINDINGS_FIX.md](BINDINGS_FIX.md) records the arrow-name correction and fresh
directional response, followed by successful actual assistant gameplay in v7.
The historical failure/diagnostic evidence above remains unchanged.
