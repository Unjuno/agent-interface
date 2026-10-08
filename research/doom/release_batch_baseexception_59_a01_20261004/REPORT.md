# Release-batch `BaseException` custody — A01

The frozen #7635 PR head accepts a release-batch exception boundary that catches `BaseException`, but `ExecutorV13` only catches `Exception`. This run tests whether a `KeyboardInterrupt` carrying `release_batch_publication` can still produce a successful terminal.

On the exact same synthetic backend, frozen head `bf57eb60009867bfa36243a9b48e37bd576682c7` emitted `status=completed`, `error=null`, and no custody receipt while the worker thread raised `KeyboardInterrupt`. The patched candidate emits `status=failed`, includes the exception and exact custody payload, and has no uncaught worker exception. `audit.py` independently checks the recorded outcomes and source hashes.

The synthetic source does not claim an actual sink delivery, physical input release, application effect, or game/task success. The separate release-backend composition tests exercise both accept-before-raise and fail-before-accept sink behavior through the current backend; these remain construction checks with fake owner/input boundaries.

Validation commands from the repository root:

```text
python research/doom/release_batch_baseexception_59_a01_20261004/experiment.py
python research/doom/release_batch_baseexception_59_a01_20261004/audit.py
python -m unittest research.doom.test_release_backend_v3_actual_composition research.doom.test_release_backend_v3_composition research.doom.test_session_map01_v13_release_telemetry research.doom.test_session_map01_v15 research.live_control.test_executor_v13 -v
python -m py_compile research/live_control/executor_v13.py research/live_control/test_executor_v13.py research/doom/test_release_backend_v3_actual_composition.py
git diff --check
```

The frozen/candidate mutation experiment reports `PASS_BASEEXCEPTION_CUSTODY_FAIL_CLOSED`. The five focused modules pass 28/28 tests, including the new direct and composed `KeyboardInterrupt` cases; `py_compile` and `git diff --check` exit 0. Command outputs and exit codes are retained alongside `RUN.json` and `AUDIT.json`.

No game, model, GUI, input, WSLc, or formal allocation was used.

Supplemental stack validation: against refreshed #7635 head `ddff6ebf8cea186accaae5dca98750ac16bb6a4b` plus this fix, the same focused command passed 31/31 tests; py_compile and diff check passed. This is a compatibility validation receipt and does not alter the frozen bf57... A01 experiment result.
