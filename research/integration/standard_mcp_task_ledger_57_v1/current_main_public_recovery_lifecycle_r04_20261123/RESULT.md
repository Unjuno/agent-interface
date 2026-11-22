# R04 result: mixed repeatability, failures retained

Disposition: **MIXED_FAKE_LOCAL_REPEATABILITY (7/10)**. This is not a reliability pass and must not be generalized to live GUI/MAP01 or production.

## Frozen denominator and outcome

The ten frozen attempts were executed once each in the order recorded in `conditions.json`; no retries or replacements were made. Normal mode passed 4/5. Optimized (`-O`) mode passed 3/5. Overall 7/10 passed. The original process exit codes are retained beside every raw log in `raw/`.

| Attempt | Mode | Exit | Outcome |
|---|---|---:|---|
| normal-01 | normal | 0 | PASS |
| optimized-01 | -O | 0 | PASS |
| normal-02 | normal | 0 | PASS |
| optimized-02 | -O | 1 | FAIL: observation failed at the fixture callback budget (receipt elapsed 8.016 s; no observation accepted). |
| normal-03 | normal | 1 | FAIL: action became uncertain and runtime returned `RUNTIME_FAILED` / `execution_failed`; release unverified, result resolution raised AssertionError. |
| optimized-03 | -O | 0 | PASS |
| normal-04 | normal | 0 | PASS |
| optimized-04 | -O | 0 | PASS |
| normal-05 | normal | 0 | PASS |
| optimized-05 | -O | 1 | FAIL: action became uncertain and runtime returned `RUNTIME_FAILED` / `execution_failed`; release unverified, result resolution raised AssertionError. |

## Interpretation

The composed exact-effect/recovery/oracle path can pass in fresh local processes, but this run does **not** establish stable repeatability under the frozen timing budget. Two action executions ended with uncertain status and unverified release; those are safety-relevant failures, not test noise. A third attempt reached the observation callback deadline without accepted evidence. These retained failures show timing sensitivity in this fixture and justify a separate bounded diagnosis of callback and release/result-resolution timing. Do not widen deadlines and rerun this frozen experiment, discard failures, or call the 7/10 result a pass.

The experiment is local and synthetic. It provides no live GUI, MAP01, WSLc, matched efficiency, preview graduation, or distributable-runtime evidence. Issue #57 remains open.

## Evidence custody

`conditions.json` and `PLAN.md` froze the question, sample count, order, thresholds, and exclusions before execution. `raw/` contains all ten process logs, all ten exit files, and the preflight write probe. `SHA256SUMS.txt` records packet-file digests. `R03` is a separately documented aborted/unscorable attempt and is not included here.