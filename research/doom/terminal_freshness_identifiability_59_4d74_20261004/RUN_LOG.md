# Run log

The plan and source were frozen before execution. The experiment ran once with Python 3.12.13 on macOS arm64, importing the vendored `ProgressClockV2` source pinned to main commit `5489741c1efa2d25bedf5aa64e60a68fb2f74e3c` (SHA-256 `3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613`). Both labeled provenance pairs emitted byte-equivalent event data: `KILL_COUNT_INCREASE` for the positive kill transition and `EPISODE_FINISHED_NO_EXIT` for the terminal transition. The clock sample API and serialized sample contained no producer epoch or update epoch. No external engine or input ran.

The independent audit passed under normal Python and `-O`; its in-memory tamper control rejected a stale-event mutation. The separately proposed ViZDoom probe was stopped before engine invocation because the exact pinned image and WAD were not available and local Python lacked `vizdoom`; see `ENVIRONMENT_STOP.md`. No install, build, pull, game, model, GUI, or formal allocation occurred.

This PASS is a counterexample to source-freshness identifiability under an explicit stale-return model. It is not evidence that the engine actually produced stale values, and it does not validate live terminal onset, gameplay effect, control cadence, or safety.
