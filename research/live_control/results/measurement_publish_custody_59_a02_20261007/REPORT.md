# Measurement publish failure custody — A02

## H

When an executor step fails with an exception carrying structured `measurement_publish_error` metadata, ExecutorV13 must preserve that metadata on the terminal release record while keeping the original step exception primary. Cleanup may succeed or fail; its outcome must not erase the earlier publication failure.

## T

Use the actual ExecutorV13 with a controlled in-memory backend. Raise `OSError("DOWN acknowledgement lost")` with a two-field measurement publication error, run the cleanup path, and inspect the emitted terminal record. Then run the full ExecutorV13 suite and attempt the related release backend/session composition suites.

## D

- RED: the new targeted test failed because `terminal.release.measurement_publish_error` was absent; terminal status remained failed and its primary error named the original DOWN acknowledgement loss.
- Repair: ExecutorV13 copies structured measurement publication error metadata into `terminal.release` after successful cleanup, and into the release record when cleanup raises an `Exception` or `BaseException`. The original step exception remains the primary terminal error; no publish retry is introduced.
- Targeted regression after repair: PASS (1/1).
- ExecutorV13 suite: PASS (14/14).
- The wider attempted composition command failed (31 failures, 1 error) because selected Doom batch-composition suites expect the `up_batch` owner implementation from `input_owner_v12.py`, which is untracked and absent from `main` in this checkout. Preserve this as a mixed-source integration limitation, not as a passing run or a regression caused by this patch.
- Python byte-compilation and `git diff --check`: PASS.

## C / U

This is deterministic in-memory executor construction evidence. It does not test an X server, Doom, GUI input, physical release, measurement sink durability beyond the supplied exception metadata, model inference, useful feedback, recovery, or task effect. This does not satisfy Issue #59's current-main live threat-control experiment. The broader mixed-source suite remains unverified as a coherent candidate.

## Commands

- RED: `python -B -m unittest research.live_control.test_executor_v13.ExecutorV13Tests.test_terminal_preserves_measurement_publish_failure_custody -v`
- Targeted: same command after the repair.
- Executor: `python -B -m unittest research.live_control.test_executor_v13 -v`
- Focused composition: `python -B -m unittest research.doom.test_release_backend_v3_actual_composition research.doom.test_release_backend_v3_composition research.doom.test_session_map01_v13_release_telemetry research.doom.test_session_map01_v15 research.live_control.test_executor_v13 -v`
- Construction: `python -B -m py_compile research/live_control/executor_v13.py research/live_control/test_executor_v13.py`
- Hygiene: `git diff --check`

Raw command output, exit codes, and SHA-256 hashes are retained in this directory. The SHA list covers the final executor/test sources, report, and primary RED/PASS/suite outputs.
