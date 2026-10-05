# Preserved failures and warnings

1. **TDD RED (expected):** before `power_model.py` existed, `python -m unittest -v` failed to import it (`ModuleNotFoundError`). This was the expected missing-implementation RED. The test suite then passed after implementation.
2. **WSLc resource warning:** construction, candidate and auditor invocations all reported that swap-limit capabilities/cgroup were unavailable. The requested 512M is not treated as verified enforcement; no memory-limit claim is made.
3. **Earlier A01 WSLc E_FAIL is separate:** it remains recorded in the A01 packet and was not retried. A02 is a new frozen allocation and its own WSLc candidate and auditor each exited 0.
4. **Audit gate projection boundary:** the frozen auditor independently recalculates the null Wilson interval and requires it to match the retained raw interval, but does not itself assert that `.0125` lies inside it. The predeclared inclusion gate was applied in the separate read-only `POSTHOC_ADJUDICATION.md`; candidate and audit outputs remain unchanged. This is retained as a limitation on how the decision gate was projected, not concealed as an auditor assertion.
5. **Host test-discovery command typo:** `python -m unittest -q -s <directory>` was rejected because `unittest` does not support `-s`; this was a command-line usage error, not a test failure. Correct discovery syntax was then used and is recorded in the final validation log.

Formal candidate/auditor STOP count for A02: zero. Candidate and auditor invocations: one each. Retries: zero.
