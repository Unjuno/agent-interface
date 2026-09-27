# Issue #3300 MAP01 clock-source setup diagnostic — 2026-09-20

Decision: `HOLD_LIVE_SPAN_UNIDENTIFIED`. This is a construction diagnostic, not the frozen formal allocation; no reliability estimate is reported.

## H/T/D/C/U

- H: determine whether the retained private MAP01 fixture supplies a changing 35 Hz episode clock under the no-input async container setup, while invoking the exact current-main scorer.
- T: OrbStack, ViZDoom 1.3.0, fixture `map01-threat-contact-v2`, MAP01 skill 1, seed 990619, hidden window then Xvfb/Openbox virtual display, `ASYNC_PLAYER` / `ASYNC_SPECTATOR`, 35 Hz, no model, network, human input, or injected keys. Frozen scorer `_coherent_progress_sample` was called once per diagnostic process.
- D: record package/map/fixture identity, scorer return, clock value before/after a one-second no-input interval, and each setup stop. The fixture manifest and save SHA-256 are checked before initialization.
- C: readiness requires a successful frozen-scorer call and an episode clock that advances during the no-input observation interval without calling an action-advance API inside that interval. This only tests clock-source availability, not phase-stratified reliability.
- U: no frozen phase/load block, no per-stratum allocation, no three-outer-attempt trace, no sample-size or all-three failure estimate. No result from #944/#1461 is rerun or relabeled.

## Observed results

Private fixture identities matched: fixture manifest SHA-256 `e57e21fd6d85d4b0720b3b3d5a52ad538fde45c50c58651ff754638f93f182e`; save SHA-256 `cc5302aa9cda3960248733caa96da1b53adcc4b6a1a2dcfb80675650c9350401`; ViZDoom 1.3.0; MAP01; seed 990619; skill 1. On load, episode tic was 1366. One call to the exact current-main `_coherent_progress_sample` returned a coherent sample. Without an action-advance call during the following one-second wait, the tic remained 1367 in both `ASYNC_PLAYER` and `ASYNC_SPECTATOR` checks (the 1367 value followed one explicit `advance_action(1, True)` startup refresh). A fresh `ASYNC_PLAYER` episode likewise remained at tic 1 for one second with no action call. The Xvfb/Openbox virtual-display run reproduced the no-input tic stall.

Therefore the container can load the private fixture and run the scorer, but the engine clock does not advance autonomously under this no-input setup. No phase distribution can be measured from these rows. Formal allocation is stopped before collection; the live-scope claim remains HOLD. Next gate: reconcile the frozen action/clock-driving contract in the MAP01 session and build a virtual-display control that advances the episode only through that already-frozen mechanism, then verify source tics while retaining every scorer bracket before freezing any phase schedule.

## Preserved setup failures

1. Hidden/no-display launch: scorer call passed, but no-input episode tic did not advance after one second.
2. `xvfb-run` first failed before game launch because `xauth` was absent.
3. After adding `xauth`, `xvfb-run` waited before child launch because its readiness helper `xdpyinfo` was absent; the exact container was observed running and then stopped. No scientific row came from these infrastructure attempts.
4. Direct `Xvfb -ac` plus Openbox allowed the scorer call, but no-input tic progression still stayed flat. No input was injected to manufacture a crossing.

## Container identity

OrbStack image ID `sha256:8d984b04efe5bca7bd9b3808aac4f56bd273a6a1ada76cd51939253b874244ca` (`linux/arm64`); runner and current-main source are in the neighboring construction path. This image is only a diagnostic image; it is not frozen for formal allocation.

Exact main/source/runtime/fixture digests and tic controls are summarized in `setup_manifest.json`.
