# Results and evidence boundary

Run date: 2026-10-05. Candidate: current main `24cbb631b972eee1723d2372adf53032dfdaab20` plus PR #8094 head `88e8099de97de12c29fcf3db0cb374b160a27ead`, with the controller conflict resolved as documented in README. The run used one decision and seed 990605.

## Hypothesis and outcome

**H:** Under a deterministic fake game/model/capture/Xlib seam, the actual V39 → V15 → V12 → V13 Executor → typed backend → owner path can complete one decision, publish observations whose typed and full artifacts reconcile, and report an empty fake-server keymap after release and cleanup.

**Outcome: PASS_CONSTRUCTION_SCOPED.** One input admission and one release transition were emitted. Five typed observations each matched a full observation by sequence and RGB SHA-256; each full artifact was exact and ready after its typed observation. The emitted owner receipt used the `keymap-batch-edge-v1` schema. The fake X server trace contains KeyPress then KeyRelease, and the final fake keymap and owner cleanup samples are empty. The scorer emitted `map_exit=false`, `player_dead=false`; child stderr is empty. The archived raw events, artifacts, source list, fake-X trace, fixture and independently runnable `audit.py` are under `raw/`.

## Limits

This is a construction test only. The fake X server causes the code's conservative keymap classifier to emit the label `CONFIRMED_PHYSICAL_UP`; the receipt also says `physical_verification_authoritative=false`, and its scope explicitly excludes physical dwell and application receipt. In this run that label means only that the fake X server's keymap transitioned from down to up. No real game, live session, actual X server, human input, model service, threat condition, or application-side consumption was exercised. The fake score contains no game-effect evidence. There is no basis here for a claim of threat exposure, improved performance, completed task, physical input release, or MAP01 benefit.

## Independent checks

- `audit.py`: PASS; checks source SHA-256 and Git blob hashes, 5/5 typed/full sequence+frame-hash reconciliations, one admission/release pair, fake X edge ordering and final state, owner cleanup state, score boundary, terminal event, and empty child stderr.
- Focused tests: 15/15 PASS (`test_v39_measurement_session_comp`, `test_map01_v15_perkey_backend_selection`, `test_map01_overlap_controller_v39`).
