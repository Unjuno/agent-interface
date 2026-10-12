# V39 health-only typed-signal monitor A01 — 2026-10-12

## H / T / D / C / U

**H:** Current main emits a typed health/ammo event before publishing the image artifact, but the reusable health-only `ObservableSignalPolicyMonitor` only handled full `observation` events and always called the HUD image reader. A validated typed health signal should let the existing health policy monitor preserve or revoke cover before artifact publication while granting no input authority.

**T:** Replay the four retained policy events from `../map01-v39-coast-liveness-live-01` through the exact health guard and the health-only monitor. Require the typed sample to reproduce the recorded policy outcome and authority fields without invoking the artifact reader, then require the same-epoch full observation to match the typed signal and RGB digest. Mismatches must fail closed.

**D:** All four samples (sequences 62, 154, 200, 218) reproduced their recorded decisions: three `SOFT_CHANGED`, one `HARD_INVALIDATED`. The health-only monitor made zero artifact-reader calls before each typed decision; matching later artifacts were coalesced. A same-epoch frame-hash mismatch produced `UNKNOWN`. The result records raw-source hashes and the local monitor Git blob.

For the hard sample (sequence 218), the runtime `emit_ns` is stamped before two event-log writes and therefore is not the stdout-delivery time. The measured `typed_emit_return_ns` is 52.310 ms after capture; artifact readiness follows 74.589 ms later; the old health-only monitor receives the full observation 6.791 ms after artifact readiness; HUD extraction then takes 22.303 ms. This trace identifies the current image-reader path as avoidable work after the pre-artifact signal exists. It does not measure the post-fix live path.

**C:** The source is frozen at main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. Raw report SHA-256: `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`; raw runtime events SHA-256: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2f3eedb381`. The guard source blob is the exact main blob `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`. Before the fix, four focused regressions failed because typed events were sent to the artifact extractor. After the fix, the focused monitor suite passed 10/10 and the V39/typed-source/Executor suite passed 133/133, both normally and under `python -O`.

**U:** This is an offline replay of retained evidence plus a local implementation test. It does not establish post-fix live event delivery, reduced end-to-end latency, useful feedback, recovery, survival, or task success. Issue #59 is unassigned and the shared WSLc lane remains under an ownership hold; no runtime, GUI, physical input, or game allocation was used.

## Reproduction

From repository root:

```powershell
$env:PYTHONPATH='research/doom;research/live_control'
py -3.11 -B research/doom/results/map01-v39-health-only-typed-monitor-a01-20261012/replay.py . research/doom/results/map01-v39-coast-liveness-live-01/report.json research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl research/doom/results/map01-v39-health-only-typed-monitor-a01-20261012/result.json
py -3.11 -B -m unittest research.live_control.test_observable_signal_guard_v2 research.doom.test_map01_overlap_controller_v39 research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_map01_overlap_controller_v39_cover_terminal research.doom.test_map01_v39_pending_observation_drain research.doom.test_session_map01_v15 research.doom.test_doom_typed_observation_epoch_exact research.doom.test_doom_typed_artifact_reconciliation_v1 research.live_control.test_executor_v13 research.live_control.test_input_owner_v12_explicit_up_cancel research.live_control.test_executor_v12_owner_release_rpc_failure
py -3.11 -B -O -m unittest research.live_control.test_observable_signal_guard_v2 research.doom.test_map01_overlap_controller_v39 research.doom.test_map01_overlap_controller_v39_dual_signal research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency research.doom.test_map01_overlap_controller_v39_cover_terminal research.doom.test_map01_v39_pending_observation_drain research.doom.test_session_map01_v15 research.doom.test_doom_typed_observation_epoch_exact research.doom.test_doom_typed_artifact_reconciliation_v1 research.live_control.test_executor_v13 research.live_control.test_input_owner_v12_explicit_up_cancel research.live_control.test_executor_v12_owner_release_rpc_failure
```