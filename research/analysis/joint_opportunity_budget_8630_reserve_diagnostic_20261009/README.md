# Issue #8630 reserve-binding diagnostic

This construction diagnostic explains the A01 weak-signal failure without changing the frozen A01 outcome. It adds a second independent recovery attempt only when observation is skipped, making the opportunity cost explicit while retaining one recovery attempt and mandatory verification for every feasible policy.

The exact model and its scope are in [MODEL.json](MODEL.json); the result and limitations are in [REPORT.md](REPORT.md). The deterministic calculator is checked against a separately written path enumerator. `PASS_DIAGNOSTIC` is scoped to this synthetic construction and is not a PASS for the full #8630 hypothesis or any runtime behavior.
