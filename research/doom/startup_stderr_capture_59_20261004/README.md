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
