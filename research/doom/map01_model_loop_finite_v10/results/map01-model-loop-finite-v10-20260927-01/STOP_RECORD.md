# v10 formal allocation STOP — seed 990636

Classification: **`STOP_CONTAINER_SOURCE_MOUNT_INCOMPLETE`**. The one-time allocation was invoked once and is permanently consumed. No retry was made.

## H/T/D/C/U outcome

- **H:** Whether changing only the inter-segment observe-only lease from 5 to 15 seconds removes the prior lease-margin HOLD and permits a later model action remains untested.
- **T:** The frozen command in `../FORMAL_FREEZE.md` was invoked once with seed `990636` and output `research/doom/map01_model_loop_finite_v10/results/map01-model-loop-finite-v10-20260927-01`.
- **D:** STOP during session startup, before the runtime emitted the expected `ready` event. The container could not import `research.observation_tiles.tile_transport` because the sparse worktree mount omitted `research/observation_tiles`. No MAP01 gameplay, refresh, input, or independent score was observed. This is a source-mount/setup failure, not a gameplay result and not evidence for or against the 15-second hypothesis.
- **C:** The v10 generated controller identity and preregistration are unchanged. Raw app-server planner protocol is retained. Preserve this seed, output path, and raw file; do not rerun.
- **U:** Lease-refresh behavior in a complete-source container; live model action continuation; task effect; MAP01 exit.

## Raw evidence

- `planner-protocol.jsonl`: 7,469 bytes; SHA-256 `1f690550e4cc2453ce4b56da50ec5de932c1df8bfe9589f4ac9a8e90bf50be9f`.
- Runner exception from the invocation: `ModuleNotFoundError: No module named 'research.observation_tiles'`, originating in `/src/research/live_control/tile_transport.py` while importing `session_map01_v12.py`.
- Container exited; no runtime events, screenshot, or score were produced.
- Root cause: the isolated worktree was sparse. The experiment adapter mounted the repository worktree read-only, so the omitted tracked package was unavailable inside the container. The host had that package in the Git tree but not in the mounted worktree filesystem.

## Required successor correction

Use a new Issue, seed, and output path. Before freezing or allocating, make the read-only source mount complete for every imported package and run a pinned-container import/startup preflight from the exact worktree mount. Verify expected `ready` and terminal/release receipts in the synthetic controls before any model-in-loop allocation. Keep the 5→15-second change isolated and preserve the prior artifacts.
