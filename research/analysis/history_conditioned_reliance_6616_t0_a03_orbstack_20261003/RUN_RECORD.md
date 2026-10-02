# Issue #6616 A03 run record

## Frozen pre-run state

- Allocation: `history-conditioned-reliance-6616-t0-a03-20261003`
- Base main after current-main refreeze: `2d5e42c2d8b9076e3b1b5f9c26cffd722f7e52aa`
- Superseded pre-run freeze: SHA-256 `20cb66a89a539469fa18761c86e33b83241569c64481bcea6d7d05d13a342498` on branch head `a74367079cfdcca20e318f139205d2608d47ca22`; main had advanced before any invocation. The refreeze is prospective; no prior candidate, auditor, container or retry count changed.
- Candidate invocations: 0; auditor invocations: 0; formal container invocations: 0; retries: 0.
- Candidate output and auditor output paths on the dedicated OrbStack VM: absent at preregistration.
- Construction contract tests: 5/5 passed locally before formal freeze. This is fixture-development evidence only.
- Human responses: 0; independent reviewer signoffs: 0/not allocated.
- A01 `STOP_CONTAINER_SOURCE_MOUNT_EMPTY` and A02 `HOLD_ALLOCATION_ID_MISMATCH` remain preserved in their separate packages and are not repaired, pooled, or rerun here.

Formal candidate/auditor receipts and output hashes will be appended after the single allowed execution. A candidate or auditor failure is terminal; do not retry or replace the allocation.
