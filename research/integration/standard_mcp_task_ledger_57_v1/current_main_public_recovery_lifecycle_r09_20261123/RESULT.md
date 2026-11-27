# R09 result: repeatability remains mixed with tracked API Futures

Disposition: **MIXED_FAKE_LOCAL_REPEATABILITY (7/10)**. Normal passed 3/5; `-O` passed 4/5. Every attempt ran once, with no retry or replacement.

The three failures were distinct:

- normal-01 and normal-05: `interface_observe` exceeded the test caller's 8-second Future timeout; the Future was still running when the timeout was recorded. The semantic test failed closed, and its finally block drained the tracked Future before temporary-directory teardown. These are callback-latency failures, not successful task effects.
- optimized-04: exact action result resolution observed a terminal action before the dispatch report finished finalizing. The test's 2-second report-finalization wait expired (`report.json` not ready); teardown then recorded `PermissionError` on the still-open `.report.json.tmp`. This reveals a detached background dispatch worker not covered by tracking only the caller's API Futures.

The other seven runs passed the exact effect, recovery release/horizon, source-UNKNOWN/null, no-replay, and independent-oracle assertions. The failures remain in the denominator. The added API-Future drain did not eliminate report-finalization races for the dispatch worker. R04 remains its own 7/10 cohort and is not overwritten or pooled into this result.

This is local Fake evidence only, not live GUI/MAP01, production reliability, efficiency, WSLc, preview, or distribution evidence. The next diagnostic must wait for the exact dispatch report and worker lifecycle to settle within a finite bound before fixture teardown, while preserving failures if the bound expires.

All ten logs, exact exit codes, conditions, source hashes, probe, and packet hashes are retained here.
