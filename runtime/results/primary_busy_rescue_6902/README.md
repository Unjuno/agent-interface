# Busy response implementation rescue: local gates remain conditional

Original source PR #6902 at `12e15aa7a3dc71a95f31ac7b600212c742dd9bff`.
Prior PR #6964 retained 140 evidence files, and #7116 retained full source history,
but neither adopted the three-line runtime backlog guard or regression module.
The two evidence packets are still source/main byte-identical. This new current-main
implementation rescue adds only the guard, original three tests, CI selection and
busy-response documentation. Keep the newer transport-exit/journal-error paragraph;
do not restore the whole older README. Old cancelled application routes/votes do
not become new authority. Original source ref remains until verified integration.

## Fresh local checks

On macOS with Node v26.7.0, before adding the guard: three methods, two FAIL and one
PASS (`node-red.log`). After adding it: three PASS (`node-green.log`). The workflow's
full 14-module Node selection: **195 PASS, zero fail/skip** (`node-selection.log`).
These are current Node26 engineering results, not the original Windows Node22
190-method receipt, nor fresh hosted Ubuntu/Node22 CI. Command UTC endpoints were
not separately captured; Node logs retain reported durations. Current kernel50
methods also passed; no kernel source is changed by this rescue.

The broader Python native contract runner **FAILED**, not PASS:

- First Homebrew Python3.14 run lacked `mcp`/`PIL`: protocol297 methods, three FAIL,
  15 ERROR, five skips; harness63 methods, one FAIL and57 ERROR. Its original
  full structured result/stream hashes are retained in `native-unprepared-result.json`.
- Separate isolated Python3.12.14 environment installed the workflow-pinned
  `mcp==1.30.0`, `Pillow==10.2.0`, `numpy==1.26.4`, `python-xlib==0.33`.
  The runner still failed on macOS: protocol426 methods, four FAIL, six ERROR,
  five skips; harness205 methods,31 ERROR. Preserve its result and complete stderr
  streams (`native-pinned-*`) without turning Linux `/proc` errors into skips.
- The four protocol assertions are `test_final_image_uses_new_call_root_without_extra_observation`,
  `test_mutated_image_preserves_result_without_rendering`,
  `test_digest_resume_rejects_noncanonical_bytes_and_read_race`, and
  `test_failed_process_reports_bounded_stderr_without_relaunch`. No unproven claim
  is made that every broader failure is environmental or caused by this guard.
  All error names/tracebacks are retained in the full streams.
- OrbStack Docker image reads stopped with content-store blob read
  `operation not supported` (including Python3.12-slim); Node22 image was absent.
  No cache prune, shared VM reuse, daemon reset or container experiment was performed.
  Linux/Node22 verification remains outstanding; local Node PASS is not a waiver.

Retained logs are unchanged local bytes, including traceback workspace paths.
Raw-inclusive whitespace checking reports seven original trailing-whitespace
lines (two Node RED, five Python harness). They are preserved, not normalized;
the authored production/config/document delta passes its separate whitespace check.
The results describe fresh engineering checks, not a formal allocation or original
producer/matrix replay. The first failure streams remain locatable by the original
result hashes in the local output directory; no successful result replaces them.

Scope: at most one unfinished busy response alongside the same committed command.
Overload can reject a responsive synchronous burst; no reply is promised for that
line. Observe/reconcile the original command/result, do not replay consumed input.
No all-byte memory bound, permanent-stall deadline, downstream consumption, native
release, physical effect or performance improvement is established.
