# R06 deterministic delayed-callback drain test

## Frozen question
When the test caller's 8-second `Future.result` expires while a fake observe worker is deliberately held, does the outstanding server coroutine remain live and complete exactly once after explicit release, and can the fixture drain it before close/tempdir teardown without an in-flight report-temp collision?

## Frozen conditions
Two fresh processes only: normal then `-O`. The test itself gates the fake observer with threading events; no input dispatch is exposed or authorized. The caller timeout remains 8 seconds. It checks that the caller times out while the future is incomplete, explicitly releases the worker, awaits the same future for at most 30 seconds, confirms a complete exact-call report/no temp file, then closes the server. No retry/replacement. See `conditions.json`.

## Interpretation
A pass proves the harness correctly drains this controlled API callback and custody file before teardown. It does not prove product reliability or reproduce the separate dispatch/result-resolution failures in R04.
