# File-presence cleanup regression qualification

## Finding and repair

`Path.is_file()` for `score.json` and `owner-events.json` is now invoked through the cleanup helper's existing `attempt` diagnostic guard. Both receipt fields start false and become true only after a successful probe returns `True`. Permission failures remain secondary cleanup diagnostics, preserve the controller exception, and leave `cleanup_complete` false.

Two focused regressions inject `PermissionError` independently at each probe and assert primary exception identity, false presence, incomplete cleanup, stage diagnostics, and failure receipt publication.

## Qualification

- Current PR head: `73dfbfda174c3525bb8f2252243e04d51e7c782b` (base `d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6`).
- Six frozen cleanup/source-refresh suites: Windows Python 3.11, 35 tests passed, 2 POSIX-only skips; WSLc, 35/35 passed, no skips.
- Eight exercised Python files compile on both environments.
- WSLc used cached image `sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378`, `--pull never`, network disabled, source mounted read-only, and separate writable output. The runtime warned that cgroup/swap enforcement is unavailable; resource limits are requested, not claimed as enforced.
- Evidence supports synthetic cleanup behavior and owned-child pipe handling only. No game, model, GUI, OS input, or live-control allocation ran; no live release or task-effect claim is made.

Outputs: `TEST_OUTPUT.txt`, `COMPILE_OUTPUT.txt`, `test-exit-code.txt`, and `compile-exit-code.txt` are the WSLc outputs; `TEST_OUTPUT_WINDOWS.txt`, `COMPILE_OUTPUT_WINDOWS.txt`, and `windows-exit-codes.txt` are the Windows outputs.
