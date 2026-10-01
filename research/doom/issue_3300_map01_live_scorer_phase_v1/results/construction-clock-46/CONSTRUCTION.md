# Construction-clock-46 — one action as API snapshot boundary

## H / T / D / C / U

- **H:** In a hidden 35 Hz `ASYNC_SPECTATOR` MAP01 session, the API/scorer snapshot remains stale during passive observation but one empty `advance_action(1)` call causes the public tic/scorer snapshot to catch up to the already-running engine.
- **T:** Three fresh sessions in the pinned arm64 ViZDoom 1.3.0 source-instrumented Docker image and Freedoom 0.13.0 WAD. Record about 1.5 s of passive `get_episode_time()` reads and the exact scorer once, issue exactly one empty `advance_action(1)`, then record public tic and exact scorer again. No other advancement call is made. Close every game.
- **D:** Preserve timed getter boundaries, before/after tic values, action call span/status, source tic-entry records, all passive reads, identities, and cleanup. Independently compare API/scorer tic before and after the single action and against engine source trace.
- **C:** This is an intervention-boundary construction diagnostic, not the passive target condition and not a formal phase/span sample. The single API action changes controller state and is explicitly labeled as intervention.
- **U:** Whether the single action exposes the full accumulated engine tic, merely one action tic, or another snapshot rule remains unknown until raw audit. Source-instrumentation uncertainty remains; formal allocation remains 0/120.

Do not infer the result from this preregistration. Raw data and audit are appended after execution.

## Observed result (construction only)

All 3/3 sessions initialized and closed. Across 116–120 passive reads over about 1.5 s, API tic stayed 1 and the exact scorer's before-action tic getters were `[1, 1]`. A single empty `advance_action(1)` returned in 2.96–16.53 ms; immediately afterward the public API reported tic 55 and the exact scorer's two tic reads both reported `[55, 55]` in all three sessions. The process-exit source trace contained 58 contiguous `vizTime` entries, ending at 58, with median entry rates 34.724–35.669 Hz.

Independent audit `PASS_CONSTRUCTION_ONLY_ACTION_BOUNDARY_CATCHUP`, zero errors. This shows that in this exact fixture the API/scorer snapshot exposed accumulated asynchronous engine progress at the action boundary; it did not expose it during passive polling. The action call is an intervention and cannot stand in for the no-action formal condition. Source timestamp uncertainty remains, formal allocation remains 0/120.
