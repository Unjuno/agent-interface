# Finish-pipe repair result

Historical baseline audit: `PASS_BASELINE_BLOCK_CONFIRMED` (14/14 checks), now reclassified as **invalid for the synchronous-write hypothesis**. Review of the retained `baseline-run-02/controller-failure.json` shows `finish_send` raised `TypeError` immediately: the probe opened stdin in binary mode, while the frozen helper writes a Python string. The worker was still alive at 0.5 s because it was waiting for the child, not because the finish write was blocked. The original result, audit, and hashes remain immutable; do not cite that PASS as evidence of pipe-write blocking.

The corrected text-mode follow-up is a separate allocation under `followup_01/`. Its sole WSLc invocation did not reach container execution: only `run-01/argv.json` was produced, and the WSLc client remained unresponsive. That owned invocation was stopped; per preregistration it was not retried. Outcome: **HOLD / infrastructure failure; no corrected baseline result**. The synchronous-write hypothesis remains unverified by this package.

The first frozen repair regression against the unchanged helper failed as expected: bounded cleanup remained blocked until the test's emergency child kill. The final frozen WSLc regression passed (1 test, 0.507 s) against the exact bytes at `research/doom/doom_controller_failure_cleanup_v1.py`. The real child did not read stdin; `finish_send` reported `timed_out`; controller cleanup retired the child, attempted planner close, preserved the original exception, and required no test-owned kill. WSLc emitted its kernel warning that swap/cgroup limit enforcement is unavailable; requested limits only are claimed.

Adjacent verification passed: 7 wait-loop tests, 2 controller behavior tests, 5 cleanup-helper tests, and 13 source-refresh tests (27 total). `py_compile` passed. `git diff --check` passed for changed production and regression files.

Scope: this demonstrates bounded cleanup for the constructed full child-stdin pipe. It does not prove physical input release, process-family cleanup, or a universal deadline.
