# WSLc offline core regression, A02

Exploratory local readiness run, not a preregistered live allocation. WSLc 3.0.3.0, pinned python image and current-main core files at bab9391daeae9f6df6452634fd4c21fc6790de78; core source was checked against both the Git index and main before execution. Network disabled, no image pull, read-only source mount, disposable unique container, one CPU requested.

All 41 tests in the three named core modules passed; raw stdout/stderr, conditions, result, exact container ID, and ID-filtered cleanup response are retained. Cleanup returned exit 0 and empty output, consistent with no matching container. The source checkout contains other experimental files, but the tested core directory matched main. This does not test real GUI, WSLc control, MAP01, model usage, real-time performance or general reliability. The observed time is not a comparative benchmark.
