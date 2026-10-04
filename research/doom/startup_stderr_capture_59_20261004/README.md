# Preserve early controller-session stderr

## H/T/D/C/U

- **H:** In the current V39 controller, child-session stderr is a `PIPE` but the parent reads it only after the normal `finish` / `process.wait()` path. If the child exits before `ready`, the wait raises without saving stderr. A sufficiently large stderr write can also fill the unread pipe and prevent the child from reaching its stdout event.
- **T:** Pin the pre-change controller at main `f2aa59c8bac88f0091eb24c4f462f55a72303d2f`. Run the new regression against that exact source, then run it against the candidate with a real local subprocess that writes 256 KiB to stderr before emitting stdout, plus a child that exits before any ready line. Run the adjacent V39 wait and controller test modules.
- **D:** Baseline must fail because the file-backed sink and stderr-path diagnostic are absent. Candidate must complete without a blocked pipe, preserve exact stderr bytes for both success and early exit, and keep the existing exited-session path nonblocking. All scoped tests and source checks must pass.
- **C:** File-backed stderr avoids an unread pipe and is available before controller success; the failure itself may still come from any startup layer.
- **U:** Synthetic local subprocesses only. No game, GUI, provider/model, live input, or stopped run was replayed. This change captures the next startup diagnostic; it does not identify the cause of the retained STOP or establish controller integration success.

## Result

The focused baseline regressions failed on the exact main source: there was no file-backed child stderr sink, and the early-exit message claimed stderr was not drained. The candidate uses `stderr.txt` as the child's file descriptor, so the parent wait loop never drains a stderr pipe. The synthetic child wrote 256 KiB before its stdout readiness line without blocking; both that output and an early-exit traceback were byte-exact in the file. The runner's early-exit exception now points to `stderr.txt`.

The candidate wait and V39 controller modules pass 10/10; Python compilation and `git diff --check` pass. Baseline and candidate outputs are in `out/`; `audit.py` independently checks the baseline source pin, expected red failures, candidate exit/test counts, and evidence hashes in `FILES.sha256`. Checks cover only this source-level diagnostic path and the existing V39 wait/controller regressions.

## Follow-up 01 — launch wiring regression

After reviewing the first result, I found that the subprocess test exercised the file-sink helper but did not assert that V39 passes that sink to its actual `subprocess.Popen` call. The follow-up adds an AST regression that requires one V39 launch, an `open_child_stderr_capture(...)` assignment to `stderr_capture`, and `stderr=stderr_capture`. This is a construction-level wiring check; it does not launch the V39 game session. The original 10-test raw output remains unchanged.

The new wiring regression fails on the exact baseline source (1 expected failure), then the updated wait/controller suites pass 11/11. Python compilation and `git diff --check` pass. The exact outputs are in `out/followup-01-*`; `FREEZE.json` records the source hashes, and `audit.py` checks this follow-up while validating the original 10-test candidate source from its retained Git commit.

## Follow-up 02 — current-main integration

After main advanced through #7577, I merged current main commit `ab63eeb452f5f305f08e9d358efe2296f4c26211` into this PR branch. The stderr change remained isolated from the comparison archive and UNKNOWN recovery changes. The wait/controller suites still pass 11/11 after the merge; compilation, whitespace checks, and the artifact audit pass. The test, compile, and diff-check outputs are retained in `out/followup-02-post-merge-*`.

## Follow-up 03 — bounded source-refresh integration

Main then advanced through #7578, which adds bounded passive refresh for unavailable HUD sources in the V39 controller. I merged current main `9590ee9e0c74f7438306e8efb48b2af813f7a86b` and ran the V39 wait, V39 controller, and source-refresh test modules together: 24/24 pass. Python compilation, `git diff --check`, and the packet audit pass. Exact outputs are in `out/followup-03-current-main-*`; the freeze binds the controller source hash to that main commit.
