# R03 result

**PASS_SYNTHETIC_FAILED_ATTEMPT_JOIN** — the focused module passed 3/3 normally and 3/3 under CPython `-O` on Windows. The App Server-reported identity and token usage passed through the v3 caller into the registered ProspectiveRun task custodian. The custodian audit returned `audited`, including `turn-ledger-1`, `thread-ledger-1`, and all five usage fields. The task projection retained `HOLD / failed_attempt_not_representable_in_v1`; finalization retained `HOLD / assigned_task_missing` with 17/18 assignments missing and `dispatch_enabled: false`.

This is a synthetic single failure-path integration result. The fake peer did not invoke a provider or GUI, and no task effect or efficiency was measured. Successful answer, deferred, unknown-usage and full matched-arm paths remain unverified. Initial failed assertion outputs are preserved and excluded. See conditions and raw logs in this directory; Issue #57 remains open.
