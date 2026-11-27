# R04 result

**PASS_SYNTHETIC_DEFERRED_AND_UNKNOWN_USAGE_CUSTODY** — 4/4 tests pass normally and 4/4 under `-O`. The new two-case check preserves (1) UNKNOWN usage on a `FAILED_UPSTREAM` attempt and (2) all five synthetic usage counters on a `DEFERRED_UPSTREAM` attempt through the v3 caller, durable allocation and registered ProspectiveRun custodian. Both custody audits succeed. Projection remains HOLD for the failed attempt and the one-task prospective run remains HOLD. The initial callback-arity failure is retained and excluded.

Synthetic adapter/caller evidence only; no provider or GUI. Does not prove success/effect, full three-arm completion, or efficiency. See raw logs and hashes in this packet; Issue #57 remains open.
