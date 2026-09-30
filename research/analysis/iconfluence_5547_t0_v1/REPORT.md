# Issue #5547 T0 — finite invariant-confluence boundary

## Disposition

Formal-01 is retained as FAIL after a stricter post-run idempotence audit exposed an unlabelled quota-reservation delta. Fresh formal-02, using explicit reservation identities, passes the scoped synthetic finite model and independent audit.

Formal-02 enumerated 100 operation/value pairs. The auditor independently checked every joined state, 10 same-delta idempotence cases, and found no invariant violation among 36 `monotone_safe` pairs. It found coordination-conflict witnesses for `REFRESH_EPOCH` (2), `RESERVE_QUOTA` (8), and `COMMIT_EFFECT` (20). Five corruption controls were rejected. Candidate, auditor and controls exited 0 in network-disabled, read-only, digest-pinned Docker Desktop containers.

Detailed results, limitations, raw first outcomes and preregistration: [formal-02 report](results/formal-02/REPORT.md), [plan](PLAN.md), [freeze](FREEZE-02.json). The earlier same-Issue Draft PR #5558 remains a separate STOP record and is not modified.

## Scope limit

This is a hand-specified finite synthetic model, not a general I-confluence classifier or proof that its state abstraction is complete. No real runtime, GUI, distributed protocol, external effect, coordination-cost reduction, or production-safety claim is established.
