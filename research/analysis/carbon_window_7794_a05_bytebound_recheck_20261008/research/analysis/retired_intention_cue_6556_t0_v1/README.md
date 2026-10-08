# Issue #6556 — post-retirement cue challenge

Finite synthetic method study only. It tests whether a retired conditional-intent response can be misattributed to a new intent that reuses the same cue, while distinguishing cue detection, event routing, response lineage, and unresolved effects/releases. No runtime behavior, human-cognition transfer, live application, or user benefit is tested.

The candidate compares cue-only, unsubscribe-only, current-generation-at-delivery, durable instance/event-ID, and origin-generation retirement-fence policies on ten frozen histories (50 case/policy rows). The independent oracle is not mounted into candidate construction or candidate execution. Its raw-only auditor checks response lineage, liveness, duplicate IDs, UNKNOWN on missing provenance, and preservation of unresolved obligations.

T0 formal receipts and scope are in [`formal_01_20261002/REPORT.md`](formal_01_20261002/REPORT.md); frozen gates and hashes are in [`formal_01_20261002/PREREGISTRATION.md`](formal_01_20261002/PREREGISTRATION.md) and [`formal_01_20261002/FREEZE.json`](formal_01_20261002/FREEZE.json). This result must not be generalized to OS queues, multi-process concurrency, real effects, or human prospective memory.
