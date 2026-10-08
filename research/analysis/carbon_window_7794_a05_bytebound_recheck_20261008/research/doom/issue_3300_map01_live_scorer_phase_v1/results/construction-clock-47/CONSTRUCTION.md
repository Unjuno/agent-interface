# Construction-clock-47 — zero-tic snapshot refresh probe

## H / T / D / C / U

- **H:** A single `advance_action(0)` can refresh the stale ASYNC_SPECTATOR controller snapshot to the already-progressed engine tic without advancing a world tic, providing a lower-intervention observation boundary than run46's `advance_action(1)`.
- **T:** Three fresh hidden MAP01 sessions, pinned ViZDoom 1.3.0/Freedoom 0.13.0, configured 35 Hz. Read passively for 1.5 s, call the unchanged exact scorer, issue exactly one zero-tic `advance_action(0)`, then read API tic and call exact scorer again. Preserve exceptions, engine trace and cleanup. This is a construction probe only.
- **D:** Independently compare passive and pre-call tics, zero-call return/error and duration, post-call API/scorer tics, source trace, and cleanup across all three sessions. No row is discarded.
- **C:** The call is still an API intervention even if zero tics are requested; it is not the no-action formal target. A successful API return alone is not evidence that the game world did not advance or that phase was reconstructed.
- **U:** Whether the API permits zero tics and whether it refreshes accumulated state without advancing remain unknown pending actual Docker run. Formal allocation remains 0/120.

## Observed result (construction only)

The exact zero-tic call returned in 3/3 sessions in 0.093–0.386 ms. It did **not** refresh the snapshot: 112–118 passive reads per session all saw tic 1, both pre-call scorer tic getters were `[1,1]`, and both post-call scorer tic getters remained `[1,1]`; public API after-call tic also remained 1. Yet each source trace contained 57 contiguous `VIZ_Tic` samples through `vizTime=57`. Independent audit disposition: `HOLD_ZERO_TIC_ACTION_DID_NOT_REFRESH_SNAPSHOT`, zero errors. This falsifies the narrow zero-tic refresh hypothesis in this fixture; it does not change formal 0/120.
