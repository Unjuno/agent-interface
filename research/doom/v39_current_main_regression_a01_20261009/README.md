# Current-main V39 model-free regression refresh (A01)

## H/T/D/C/U

- **H:** the retained V39 observation, dual-signal cover, terminal-release, pending-observation-drain, and V15 measurement-session regression set still passes after `main` advanced beyond A14's pinned source commit.
- **T:** on exact `origin/main` `743ae74ec5be2472ff27fa06fe13d5ecf8534de5`, run five existing unittest modules in normal and optimized Python modes using the Codex-bundled Python 3.12.14 runtime. No game, model, GUI, OS input, or container is started.
- **D:** PASS only if both modes run all tests with exit 0 and the independent audit verifies all pinned source blobs and raw test output.
- **C:** this is a model-free source regression check. It does not expose a live threat, prove that threat evidence interrupts a pending model answer, measure physical per-key release, establish independently useful feedback or recovery, or demonstrate MAP01 progress/completion.
- **U:** the result determines whether this regression baseline is still executable on current main and identifies the precise source drift since the prior A14 pin. It does not authorize or replace the live allocation.

## Result

PASS: 81/81 tests in normal mode and 81/81 under `python -O`. The prior A14 source pin at `cb3fb7cea16ab57c5474164dc17b88f7ff51daa9` covered 45 files; 3 of those changed by current main. The full current test import closure contains 47 unique files, including the previously omitted `test_running_action_guard_v2` fixture and its dependencies; two files are additions to the prior 45-file pin set.

Changed files among the prior 45 pins:

- `research/doom/doom_controller_failure_cleanup_v1.py`
- `research/doom/test_map01_overlap_controller_v39.py`
- `research/doom/test_map01_v39_pending_observation_drain.py`

The V39 controller implementation and `session_map01_v15.py` source blobs remained unchanged from the A14 pin. The three changed files were included at current-main identities in this run.

The run used the bundled Python 3.12.14 runtime with Pillow 12.3.0. Initial attempts with the system Python lacked Pillow; the first extraction also omitted a test helper import. Those were harness/setup failures, not counted as candidate test failures. The complete 47-file closure was then extracted from the frozen commit and both full commands passed.

## Reproduction

From a checkout containing the frozen commit and the 47 files in `SOURCE_PINS.json`, set the working directory to `research/doom` and run the two exact commands in `COMMANDS.txt`. This package preserves the current-main identities and output from the completed run. `audit.py` independently checks git blob IDs, SHA-256 values, source drift, and the two retained unittest transcripts; it does not rerun the tests.

## Scope boundary

The Issue #59 live threat-exposure gate remains open. This result does not establish any physical input state, live application effect, task efficacy, survivability benefit, or terminal outcome. No live allocation was run or authorized.
