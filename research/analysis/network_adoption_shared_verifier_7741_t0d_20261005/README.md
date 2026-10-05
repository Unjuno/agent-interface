# Issue #7741 T0d preregistered shared-queue spillover contrast

This is a new, additive allocation following the retained T0/T0b/T0c outcomes. The T0c result remains `METHOD_FAIL_OR_INCONCLUSIVE`; its per-principal comparator had 11/16 positive p95 differences, so T0d estimates the peer-minus-frozen change in shared-one-server p95 minus that same change in per-principal queues. The allocation uses eight fresh seeds, two topologies, two imitation values, fixed 160-tick runs, and the unchanged synthetic event model.

The protocol is frozen in `protocol.json`; source hashes and no-retry rule are in `FREEZE.json`. The primary seed-level criterion is shared-queue p95 increase > 0, spillover difference-in-differences >= 3 ticks, and increased unfinished obligations. The practical threshold equals the model's service duration; it is not empirically calibrated. A scoped pass requires >=6/8 qualifying seeds in every topology-by-imitation cell, a clean independent event/accounting audit, and exact null differences in the no-imitation and shared-24 controls. No grid expansion is allowed.

The construction suite is run before the formal invocation. The one-shot runner records separate candidate/auditor stdout, stderr and exit receipts, binds raw output to hashes, and refuses to overwrite an existing formal directory or run against changed source. A failed execution or audit is preserved without retry.

This deterministic integer-tick enumeration makes no claim about host performance, real users, production capacity, safety, or external adoption behavior. Formal outcome and retained raw evidence will be appended to `REPORT.md` after the one-shot run.
