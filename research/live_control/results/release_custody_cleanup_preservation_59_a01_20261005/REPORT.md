# Cleanup failure preserves prior release custody — A01

## H

If a step raises an exception carrying `release_batch_publication` and the subsequent `release_all()` raises without a replacement ledger, ExecutorV13 must still put the original delivery ledger on the failed terminal record.

## T

Current stack parent: PR #7635 head `dd5e7fa4b26c66fe1de3bfa24152ad8e4e8a9cfd`. Its `executor_v13.py` blob is identical to the prior frozen parent `636f61941e3da887a1641e4399c2f0e3373a7974`, where the RED reproduction was recorded.

The regression uses the real ExecutorV13 worker with a controlled backend. Its step raises a `RuntimeError` carrying a one-position `unknown` ledger; cleanup then raises an `OSError` with no ledger. The expected terminal is `failed`, carries the exact step ledger, invokes cleanup once, and retires the active intent.

## D

- RED on the prior parent: terminal was `failed`, but `release.release_batch_delivery` was absent (`None` instead of the expected exact ledger). The executor source blob is unchanged at the current parent.
- Candidate regression: 1/1 PASS.
- Focused release backend, session, and executor suites: 34/34 PASS.
- Python byte-compilation and `git diff --check`: PASS.

## C / U

This is deterministic in-memory backend/executor construction evidence. It does not exercise an X server, a game, model inference, GUI, native input, physical key release, useful task feedback, bounded recovery, live allocation, or task effect. It does not close the live #59 threat-control gate.

## Commands and records

- `python -B -m unittest research.live_control.test_executor_v13.ExecutorV13Tests.test_cleanup_failure_preserves_prior_step_delivery_custody -v`
- `python -B -m unittest research.doom.test_release_backend_v3_actual_composition research.doom.test_release_backend_v3_composition research.doom.test_session_map01_v13_release_telemetry research.doom.test_session_map01_v15 research.live_control.test_executor_v13 -v`
- `python -B -m py_compile research/live_control/executor_v13.py research/live_control/test_executor_v13.py`
- `git diff --check`

Raw outputs, exit codes, source/test hashes, and the independent transcript audit are in this directory.
