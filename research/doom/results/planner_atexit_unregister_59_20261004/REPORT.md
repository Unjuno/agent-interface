# Planner atexit callback after bounded close timeout

## H/T/D/C/U
- **H:** On exception, `ControllerFailureCleanup` runs a bounded `planner.close(timeout=1)` on a daemon worker. If it times out, the separate `atexit.register(planner_client.close)` remains installed and can synchronously call the same non-cooperative close during interpreter shutdown, hanging exit after the receipt is written.
- **T:** Register the exact bound close callback in a modeled registry, induce a never-returning close, and inspect callback removal, primary error identity, and receipt status. Compare helper from PR #7598 head `6c8a71d7a8897ccba4fe99f8322dba9414bb6bde` to the repair. Run the six frozen cleanup/source-refresh suites on Windows and WSLc.
- **D:** PASS requires the callback to be removed, `planner_close` to remain `timed_out`, and `cleanup_complete=false`; the primary exception must remain unchanged.
- **C:** Unregistering the callback could be ineffective for bound methods or alter successful cleanup. The modeled registry checks bound-method equality; full suites exercise successful cleanup. A timed-out daemon close worker may still remain active, so this change does not prove planner shutdown or cleanup completion.
- **U:** The unit test models Python's atexit registry calls and does not run actual interpreter shutdown or the app-server client. No runtime/game/input behavior is measured.

## Result
The exact PR-head helper fails the new regression: the bound `close` callback stays in the modeled registry after the bounded close reports `timed_out`. The repair always attempts `atexit.unregister(self.planner.close)` after the bounded close attempt. Candidate passes the regression; the original error remains raised, `planner_close` stays `timed_out`, and `cleanup_complete` stays false.

Frozen six-suite results: Windows Python 3.11 ran 33 tests with 2 POSIX-only skips; WSLc ran 33 tests with no skips. Compilation and `git diff --check` passed. WSLc warned that cgroup/swap enforcement is unavailable; 1 CPU and 512m were requested, not verified as enforced. Container list was empty after the `--rm` run.

## Scope
This fixes the interpreter-exit re-entry path. A non-cooperative planner close worker can still remain alive; the receipt correctly remains incomplete. It does not certify planner release, live input release, score, threat control, or task success. No game, model, GUI, OS input, or formal #59 allocation ran.

## Artifacts
`FREEZE.json`, `RUN.json`, `STATIC_CHECKS.json`, baseline/candidate test output and exit files, `baseline/` exact source fixture, and `SHA256SUMS` preserve the source and execution record.
