# Issue #6689 — finite prefix-stability T0

**Final preregistered decision: `FAIL_METHOD` (posthoc adjudication).** The original raw-only auditor emitted `PASS_METHOD_SCOPED`, but both candidate and auditor suppress an unresolved mandatory-check-vector obligation after a decisive mandatory failure. This violates the frozen decision rule; 192 retained stable-negative states exhibit the defect. Candidate/auditor/retries remain 1/1/0; no rerun. See [adjudication](formal_01_20261002/ADJUDICATION.md) and [preserved raw auditor result and qualification](formal_01_20261002/RESULTS.md).

This is authored finite-state method evidence only; no live verifier, action-safety, or latency claim. See [preregistration](PREREGISTRATION.md) and [freeze](FREEZE.json).

## Run identity and coexistence

This packet is allocation `PREFIX-STABILITY-6689-T0-20261002-01`, frozen from main `b711b7781cabcf23d40d078c376ffad52bd33201`. It is distinct from allocation `PREFIX-STABILITY-CERTIFICATE-6689-T0-20261002-01`, whose separate `FAIL_AUDIT / STOP_CLASSIFICATION_COUNT_CONTRACT` result is retained in the original `prefix_stability_6689_t0_20261002/` path and PR #6704. That auditor-exit-2 result is not the auditor-exit-0 receipt or posthoc `FAIL_METHOD` adjudication in this packet. The preregistered packet was initially stored at `prefix_stability_6689_t0_20261002/`; after the separate allocation appeared at that same path, this packet was moved to its current unique directory without editing file contents. `SHA256SUMS.txt` records all retained packet files, allowing both immutable records to coexist without overwrite.
