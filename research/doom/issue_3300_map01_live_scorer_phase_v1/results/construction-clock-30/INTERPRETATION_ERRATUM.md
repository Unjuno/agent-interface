# Interpretation erratum — construction-clock-30

This note supplements the immutable run-30 raw capture and audit. It does not
change their hashes, status, or construction-only allocation.

The audit label `HOLD_PASSIVE_ASYNC_TIC_STATIC_PROCESS_IDLE` is too strong if
read as a finding that the simulation clock itself is idle. Run 30 measured
only the ViZDoom child process state at two boundaries (`S`), low process CPU
ticks, and an unchanged Python-visible episode tic. None is a direct observation
of the engine's live `gametic` or map tic. The defensible empirical result is:
the Python-visible tic stayed static in these three sessions, while the child
was mostly sleeping and the unchanged scorer returned 3/3.

## Source basis (upstream tag 1.3.0)

- `src/vizdoom/src/d_net.cpp`: `TryRunTics()` calls `VIZ_AsyncStartTic()` in
  controlled async mode, then runs the available game tics.
- `src/vizdoom/src/viz_main.cpp`: `VIZ_AsyncStartTic()` invokes
  `VIZ_MQTic()`; `VIZ_Tic()` calls `VIZ_GameStateTic()` only when
  `vizNextTic` is true.
- `src/vizdoom/src/viz_message_queue.cpp`: in async mode `VIZ_MQTic()` uses
  `VIZ_MQTryReceive()`; it sets `vizNextTic` for controller `TIC` or
  `TIC_AND_UPDATE` messages. Without such a message, no state refresh is
  requested at that boundary.
- `src/vizdoom/src/viz_game.cpp`: `VIZ_GameStateTic()` writes `GAME_TIC` and
  `MAP_TIC` into shared memory.
- `src/lib/ViZDoomController.cpp`: Python-visible `getEpisodeTime()` reads the
  mapped `gameState->MAP_TIC`; `advanceAction()` sends tic messages and can
  request `updateState()`.

Together these paths make stale shared state and a sleeping child compatible
with engine work whose current tic was not independently sampled. The run-30
CPU measurement cannot determine which occurred. Also, its `/proc` samples only
captured process state initially and at the end; they do not establish that it
remained asleep throughout the interval.

## Corrected disposition and next experiment gate

Corrected interpretation: `HOLD_LIVE_TIC_UNOBSERVED`; no independent live-tic
witness, phase estimate, or 35 Hz progress result was obtained. Do not use run
30 to authorize formal collection. The next construction step must observe the
engine's live tic without sending a controller tic/update message or reading a
stale `MAP_TIC` snapshot. Any observer instrumentation must be shown not to
perturb the frozen scorer boundary and must be frozen as part of a separate
construction protocol before a formal allocation is considered.

Follow-up construction work (runs 31–33) now supplies an internal-tic
observation and a separate failed clock-alignment attempt. Run 32 observed
contiguous `VIZ_Tic` progress under debug instrumentation while the Python
snapshot stayed at 1; it is construction-only and does not establish phase.
Run 33's Docker timestamps and container monotonic values lacked a measured
cross-clock offset/drift bound, so scorer-to-engine phase remains unobserved.
See the separate immutable run records; neither changes run 30's capture or
original audit.

## Reproduction status

No experiment was rerun for this correction. It is a source-level
reinterpretation of retained run-30 evidence. The exact experiment remains
`raw.json` SHA-256
`b892a8e9fb12a98d3ac8162c2712bdc05cea75c61bcc2bfcb95f01fe0b5cc2cd` and its
original audit remains unchanged.
