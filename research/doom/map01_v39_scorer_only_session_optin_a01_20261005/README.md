# MAP01 V39 scorer-only session opt-in A01

## H / T / D / C / U

**H:** The current V39 runner can opt into the existing V15 measurement session, retaining V12 as its default, so a later authorized current-main exposure can record per-key release telemetry and scorer-only kill/death/terminal events without publishing scorer state into controller events.

**T:** Against base main `54af15a28d7d6d10d05221014ddf7a75d73b3e49`, add an explicit `--measurement-session` selector and verify that it changes only the child session path and records the selected mode. Re-run the existing V39 selection, V15 lifecycle/source-composition, and scorer-file/event contract tests. Freeze exact source hashes in `FREEZE.json`.

**D:** PASS_SOURCE_SELECTION_ONLY iff the flag-off path remains `session_map01_v12.py`, flag-on selects `session_map01_v15.py` with identical remaining CLI arguments, V15/source tests pass, and scorer-only output stays controller-invisible.

**C:** V15 wraps the unchanged V12 session with owner-thread per-key release receipts and a main-thread scorer clock. Its release measurements and scorer samples are source-construction capability; they do not verify the V39 outer controller's live process composition, a threat exposure, or temporal task-effect attribution.

**U:** No model, DoomGame, GUI, X server, OS input, container, or live allocation was run. No useful task effect, bounded recovery, threat response, survival, or MAP01 outcome is established. The Windows anonymous-pipe polling test is unsupported on this host and remains unverified here.

## Result

`python -B -m unittest -v test_map01_overlap_controller_v39`: 5/5 passed.

`python -B -m unittest -v test_session_map01_v15`: 8/8 passed.

`python -B -m unittest -v -k event_clock -k non_progress -k scorer_files -k terminal_repeat test_map01_scorer_stdio_adapter_v1`: 4/4 passed.

`python -B -m py_compile research/doom/map01_overlap_controller_v39.py research/doom/test_map01_overlap_controller_v39.py` and `git diff --check` passed.

The targeted checks satisfy the source-selection gate. The anonymous-pipe test did not pass on this Windows host (`select.select` raised `WinError 10038`); it is recorded as unverified rather than counted as a regression pass.
