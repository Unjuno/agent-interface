# #1739 retained integrity failure

The first post-freeze execution detected a Git-blob mismatch for the locally materialized `classify.py`. The wrapper should have stopped immediately but did not use fail-fast shell semantics, so it continued and generated a candidate RESULT/AUDIT locally.

Those post-mismatch outputs are **invalid and are not retained as scientific evidence**.

The scientific classifier was therefore not validly executed under the preregistered exact-source condition. #1739 is retained as `FAIL_INTEGRITY`; it is not rerun or relabeled.

A successor may change only materialization/execution plumbing: execute directly from an exact Git checkout and enforce a hard stop before scientific execution on any identity mismatch. The fixture, classifier logic, H/T/D thresholds, and predecessor evidence remain unchanged.
