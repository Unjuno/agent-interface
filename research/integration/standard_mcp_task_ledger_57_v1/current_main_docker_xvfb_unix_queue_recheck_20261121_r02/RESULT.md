# R02 launch-preflight result

Status: `HOLD_RUNNER_PRECONDITION`.

The first isolated-container launch was attempted before the frozen R02b rerun. Docker rejected the runner before Xvfb or the selected test started because the host-created `/evidence/runs/normal` directory already existed and the runner's `mkdir` refused it. Captured output is in `runs/normal/container.stdout.log` with host exit code 1. No X server or test process was launched and no queue/release result was produced.

This is retained as a launch-procedure failure only. R02b uses a fresh packet with empty precreated output folders and an explicit empty-folder check; its normal and optimized results are independently retained and audited. Do not count this preflight as a test attempt or product outcome.
