# Issue #59 planner-close deadline follow-up

## H / T / D / C / U

**H:** A planner implementation that ignores `close(timeout=1)` can keep pre-input failure cleanup from returning or publishing its receipt. Running planner close in the existing bounded daemon-worker path should let the controller return at the deadline, preserve the primary exception, and mark cleanup incomplete.

**T:** Inject a planner whose close blocks forever. Compare the parent commit with the candidate: parent must hit an external 0.75 s watchdog; candidate must return within 2.5 s, publish `controller-failure.json`, retain the injected `ValueError`, record `planner_close=timed_out`, and keep `cleanup_complete=false`.

**D:** The parent hit the watchdog without a receipt. Candidate returned in 1.009 s and satisfied all five receipt/error conditions. The focused cleanup, portability, and stage suite plus existing V39 wait-loop and source-refresh suites passed 31/31.

**C:** This is a synthetic Python client-boundary injection. It proves only that the controller stops waiting and records uncertainty. It does not cancel the worker, prove planner/process termination, establish physical key release, or qualify a game/scorer runtime.

**U:** The non-cooperative daemon worker may continue after the controller writes its receipt. Any stronger guarantee requires a cancellable client operation or process-level isolation and a separate experiment.

## Frozen inputs and commands

- Repository: `Unjuno/agent-interface`
- Parent source commit: `2559e5e6682fc6833aa4178a206ba0603e538dc0`
- Candidate working source: this package's parent worktree immediately before the follow-up commit; helper SHA-256 is recorded in `RAW.json`.
- Host/runtime: macOS local Python 3; no container or game runtime is required for this narrow client-side timing discriminator.
- Fault: `StuckPlanner.close()` blocks on `threading.Event().wait()` and ignores its timeout argument.
- Baseline watchdog: 0.75 seconds. Candidate external watchdog: 2.5 seconds. Expected planner deadline: 1.0 second.
- Focused command: `python3 -m unittest -v test_controller_failure_cleanup_v1 test_controller_failure_cleanup_portability_v1 test_controller_failure_cleanup_stage_v1 test_overlap_controller_v39_wait test_source_refresh_v1` from `research/doom`.
- Candidate fault runner: `python3 research/doom/results/issue59_planner_close_deadline_followup_20261004/run_followup.py` from repository root.

The helper's timeout is treated as a caller wait bound, not cancellation. A timeout cannot count as successful cleanup.
