# ASYNC_SPECTATOR scorer-refresh qualification A01

This is one neutral, headless ViZDoom runtime qualification for the #59 scorer-checkpoint question. It does not consume the separately unassigned private X11/game/model recovery lane.

## H/T/D/C/U

**H.** For the exact MAP01 session mode used by the pinned v15 composition (`ASYNC_SPECTATOR`, ViZDoom 1.3.0, Freedoom 2 MAP01), the prospective scorer checkpoint's exact-one-episode-tic acceptance rule may reject a successful `advance_action(1, True)` state refresh. The measured quantities are `DoomGame.get_episode_time()`, `GameState.tic`, and the same `GameState.game_variables` snapshot; scores remain no-authority data.

**T.** Run one fresh CPython process with the exact 1.3.0 macOS arm64 wheel and bundled Freedoom WAD, seed 40104, ticrate 35, hidden window, SDL dummy driver, no available buttons, and zero model/X server/GPU. Record initial, after-passive-150-ms, before-update, after-update, and after-another-passive-150-ms snapshots. Call `advance_action(1, True)` exactly once. Preserve stdout, stderr, host exit, raw result, source pins and hashes.

**D.** PASS_COUNTEREXAMPLE if setup/version/WAD/mode/button/close gates pass, the update returns, the state snapshot tic advances, and the episode-tic delta is greater than one. PASS_NO_COUNTEREXAMPLE_IN_SINGLE_RUN if the update returns with a snapshot tic advance and delta at most one. STOP/FAIL for mismatch, no snapshot advance, nonempty buttons, process failure, or failed close. Do not infer generality from one process.

**C.** Prior ASYNC_PLAYER evidence already showed a 1→8 episode-time change; this run changes the mode to the target ASYNC_SPECTATOR. An alternative explanation for the earlier passive non-advance is getter/engine scheduling; this run directly records both episode time and snapshot tic around an acknowledged update. No score changes in this neutral state, so this does not prove freshness for changing KILLCOUNT/DEATHCOUNT values.

**U.** Native macOS 27.0.1 arm64 / CPython 3.14.5 was used because OrbStack's daemon returned a content-store `operation not supported` error for an image inventory request. This is not an OrbStack/WSLc/X11 result. It is one short engine process only; it does not show GUI behavior, physical input release, useful task effect, planner resumption, bounded recovery, or a live MAP01 outcome. No game/model/X server/GPU/positive input or output-affecting task command was used.

## Result

`SCORER-REFRESH-59-ASYNC-SPECTATOR-01` is `PASS_COUNTEREXAMPLE_EXACT_ONE_TIC_GUARD`: passive 150 ms left both episode and state tic at 1; the single acknowledged update returned in 4,014,833 ns with episode time 1→11; the returned `GameState.tic` was 11. The exact-one-tic gate would reject this valid update interval. KILLCOUNT and DEATHCOUNT stayed 0 in both snapshot and live reads. `game.close()` returned. This qualifies a false-rejection boundary, not scorer-change attribution.

The saved raw record is audited by the separate `audit.py` implementation. It checks the exact run source hash, package/WAD/mode, no-button/no-positive-input source, checkpoint sequence, result classification and close receipt. It does not rerun the game. Result and retained hashes are in `audit.json` and `SHA256SUMS`.

## Reproduction

The measured run used the native CPython 3.14.5 venv and the exact wheel `vizdoom-1.3.0-cp314-cp314-macosx_14_0_arm64.whl` (SHA-256 in `freeze.json`), downloaded from PyPI with `pip download --only-binary=:all: --no-deps --platform macosx_27_0_arm64 --implementation cp --python-version 314 --abi cp314 vizdoom==1.3.0`. The wheel's bundled `freedoom2.wad` SHA-256 is pinned in the freeze. NumPy 2.5.2 came from the host's system-site-packages; gymnasium/pygame wrappers were not installed or used.

Run command (a new run must use a new allocation ID; do not replay this retained A01):

```sh
.venv/bin/python experiment.py
.venv/bin/python audit.py
```

The current runtime interpretation follows the official [ViZDoom DoomGame API](https://vizdoom.farama.org/api/python/doom_game/) and [GameState API](https://vizdoom.farama.org/api/python/game_state/): an acknowledged `advance_action(..., update_state=True)` updates state; a `GameState` contains game variables and a `tic`. The observed 10-tic jump does not establish why passive time remained unchanged.
