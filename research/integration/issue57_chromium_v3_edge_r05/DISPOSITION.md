# R05 disposition

The frozen R05 run returned `TASK_SUCCEEDED` through the current v3 caller and
compiled core. Saved observations show exact OCR for `t991025-3` before Submit,
then a changed submission page. The server recorded exactly one POST with
`value=t991025-3`; the core receipt records one completed transition and
verified release. Source/capture hashes match, Edge returned 0, and the
test-owned profile/temp root were removed. The full caller result was written
before assertions.

Both normal and `-O` invocations of the frozen auditor returned `HOLD` only
because the copied auditor still hardcoded the R04 token (`t991025-2`) instead
of using the frozen R05 conditions token. The raw mismatch and both audit
outputs are retained. The test source, POST, and conditions independently
agree on `t991025-3`, but R05 remains HOLD under its frozen auditor. R06 uses a
fresh token and an auditor that derives the expected value from its frozen
conditions; R05 is not rerun or rewritten.

This remains a single prepopulated-token Submit smoke with an offline model
fixture. It does not test generation changes, two-action entry, external model
cost, matched efficiency, recovery, MAP01, or runtime readiness.
