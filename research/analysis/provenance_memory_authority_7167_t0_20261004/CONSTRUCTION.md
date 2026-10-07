# Pre-freeze construction record

All tests in this file ran before the source freeze. They are not formal
candidate/auditor invocations or evidence for `PASS_METHOD_SCOPED`.

1. Initial construction test run: 1 failure, 2 passes. Two expected contract
   digests were absent because in-memory tests called the pipeline directly;
   the CLI attaches those digests. Fixed the test helper to reproduce the
   formal raw-output envelope. Candidate logic was not changed for this issue.
2. Second construction test run: 1 failure, 2 passes. The expected active
   intent list used the wrong order; the implementation sorts by contract key.
   Corrected the test expectation to the frozen key order.
3. Final construction test run: 3/3 passed. `py_compile` and
   `git diff --check` passed. The one-shot formal CLI pair has not run.

These failures are preserved here as construction-stage test observations;
they are not silently counted as formal failures or candidate retries.
