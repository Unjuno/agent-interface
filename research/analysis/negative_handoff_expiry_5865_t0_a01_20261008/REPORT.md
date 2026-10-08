# Issue #8466 — source-time expiry across negative-evidence handoff

## Result

`PASS_METHOD_SCOPED` for the frozen finite logical-time method fixture. A forwarded receipt with a source-time expiry of 10 was still `NO_MATCH` under the receiver-relative sliding-TTL control at C02 time 16, while the source-bound absolute-expiry arm correctly returned `EXPIRED`. The independent auditor reconstructed all 10 cases and rejected all six frozen output mutations.

The fresh source re-evaluation (C03, epoch 2, expiry 24) remained eligible and returned `NO_MATCH`. Invalid clock/epoch/scope/query/expiry cases remained `UNKNOWN`; timeout remained `TIMEOUT`; authority was false in every case. At the exact boundary (C07, time 10), absolute expiry returned `EXPIRED` while sliding TTL returned `NO_MATCH`.

## Execution and integrity

- Candidate: one container invocation, exit 0; auditor: one separate container invocation, exit 0; retries: 0.
- Runtime: OrbStack Docker Engine 29.4.0, Linux/arm64, pinned Python image digest recorded in `RUN_RECORD.json`; network disabled and root filesystem read-only. Limits were requested; effective enforcement is not independently claimed.
- Frozen source/input/oracle hashes and preregistered protocol are retained in `FREEZE.json` and `SHA256SUMS.txt`. Raw output and independent audit are retained unchanged in `formal_01/RAW.json` and `audit_01/AUDIT.json`.
- This is a logical-time finite-method result only. It does not establish real cache behavior, clock synchronization, producer correctness, GUI/runtime effects, task benefit, latency, or safety.

## Reproduction boundaries

The one-shot formal commands and isolation boundary are in `PREREGISTRATION.md`. Formal candidate/auditor invocations must not be repeated. The host construction tests are separate, non-formal checks and may be run locally without using the auditor-only oracle in the candidate container.
