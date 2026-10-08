# Notification identity rescue: current-main revalidation

Date: 2026-10-08 JST

## H/T/D/C/U

- **H:** A nested `wait_notification` predicate can consume queue entries while an outer wait is active; an outer wait must re-scan newly queued rows instead of sleeping or reporting EOF with an eligible item still queued.
- **T:** Recompose the preserved R03 source/tests onto current `main` and run the focused notification/reader/EOF regressions, archive receipt checks, local native runner, and repository indexes.
- **D:** Candidate was first composed onto `6da5dc940fdb97866cfb900ca747edb8c94b2790` (merge commit `4f05e03af6696844fcc55e5d8e57b77fb6399347`), then latest main `ffd4544a4816ded386616e8e614b5a17e6c992ef` was merged (see branch history). The old-main PR #8334 code delta is 19 additions/3 deletions to the client and two regression modules plus its 16-entry archive. Current-main arrival fixture correction adds initialization of `_journal_order_lock` to its constructor-free test client; it does not change production source. Predecessor #7087 remains unchanged.
- **C:** Eight focused app-server/notification modules: 39/39 PASS in normal mode and 39/39 under `python -O` on CPython 3.12.13, repeated after composing latest main `ffd4544`. The first current-main run identified two fixture failures because the manually allocated client omitted the lock used by `_read`; after adding that required fixture state, both normal and optimized runs pass. Archived SHA256SUMS: 16/16 PASS. Workspace index: 161 top-level dirs PASS; strict analysis index: 775 retained result dirs PASS; `git diff --check` PASS.
- **U:** `runtime/integration_checks/native.py` was run on base `6da5dc940fdb97866cfb900ca747edb8c94b2790` and is **FAIL**, not PASS. Protocol: 454 tests, 3 failures, 15 errors, 5 skipped; harness: 64 tests, 1 failure, 57 errors; win32: 36 tests, 11 errors, 8 skipped. Failures include missing `mcp`/`PIL`/`Xlib` dependencies, Linux `/proc` assumptions on macOS, and unrelated existing path/race/image diagnostics. Exact `result.json` and all six runner logs are retained under `results/local_native_ci/`; the full runner was not repeated after the unrelated latest-main update. This is synthetic queue/reader contract validation, not an app-server service, model, GUI, task-effect, or product result. Existing PR #8334 still requires fresh nonauthor review; no approval has been submitted or inferred. Keep PR Draft and do not merge main until review and required current-head checks pass.

## Commands

Focused module names and exact commands are in `COMMANDS.txt`. Local native runner invocation is recorded there; its raw output is preserved next to this report.
