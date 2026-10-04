# Finish-pipe repair result

Frozen baseline audit: `PASS_BASELINE_BLOCK_CONFIRMED` (14/14 checks). The baseline filled the child pipe to 65,536 bytes; cleanup remained blocked at 0.5 s and planner close had not run. After the probe killed its owned child, the cleanup thread completed. Baseline result and its source/report hashes remain immutable.

The first frozen repair regression against the unchanged helper failed as expected: bounded cleanup remained blocked until the test's emergency child kill. The final frozen WSLc regression passed (1 test, 0.507 s) against the exact bytes at `research/doom/doom_controller_failure_cleanup_v1.py`. The real child did not read stdin; `finish_send` reported `timed_out`; controller cleanup retired the child, attempted planner close, preserved the original exception, and required no test-owned kill. WSLc emitted its kernel warning that swap/cgroup limit enforcement is unavailable; requested limits only are claimed.

Adjacent verification passed: 7 wait-loop tests, 2 controller behavior tests, 5 cleanup-helper tests, and 13 source-refresh tests (27 total). `py_compile` passed. `git diff --check` passed for changed production and regression files.

Scope: this demonstrates bounded cleanup for the constructed full child-stdin pipe. It does not prove physical input release, process-family cleanup, or a universal deadline.
