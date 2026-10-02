# Issue #6689 — finite prefix-stability T0

**Final preregistered decision: `FAIL_METHOD` (posthoc adjudication).** The original raw-only auditor emitted `PASS_METHOD_SCOPED`, but both candidate and auditor suppress an unresolved mandatory-check-vector obligation after a decisive mandatory failure. This violates the frozen decision rule; 192 retained stable-negative states exhibit the defect. Candidate/auditor/retries remain 1/1/0; no rerun. See [adjudication](formal_01_20261002/ADJUDICATION.md) and [preserved raw auditor result and qualification](formal_01_20261002/RESULTS.md).

This is authored finite-state method evidence only; no live verifier, action-safety, or latency claim. See [preregistration](PREREGISTRATION.md) and [freeze](FREEZE.json).
