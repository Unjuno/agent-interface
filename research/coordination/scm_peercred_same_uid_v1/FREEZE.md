# SO_PEERCRED identity granularity v1 — source-first freeze

Task: COORD-PEER-IDENTITY-GRANULARITY-20260917-024
Issue: #594
Publication BASE: 61ebe01b5fbf2632dcd636b975851487617ff14b
Scope: research/coordination/scm_peercred_same_uid_v1/**

Formal A1 is exactly plan.json: 12 fresh first outcomes, six independently invoked 2-case chunks. The authorized helper and experimental task both run UID/GID65534, but have distinct PIDs. Single factor is broker identity granularity: `uid_only` authorizes any peer UID65534; `uid_pid` authorizes only the exact preregistered helper PID+UID. The task, owner socket, broker socket mode, DB permissions, decision, mutation and check+commit semantics remain fixed. No retries, token refresh, helper replacement, identity-policy changes or post-result tuning.

Pinned dependency from immutable BASE: `research/coordination/scm_peercred_gate_v1/run_case.py` Git blob `97ec6bb6f85e5a31ee63e13bebe74af162898518`; reused only for schema/owner/read-token commit/snapshot mechanics.
