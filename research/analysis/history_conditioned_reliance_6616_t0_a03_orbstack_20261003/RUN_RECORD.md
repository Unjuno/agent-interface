# Issue #6616 A03 run record

## Frozen pre-run state

- Allocation: `history-conditioned-reliance-6616-t0-a03-20261003`
- Base main after current-main refreeze: `5e9d5b3e8d1f5685ccd71fc1ebb50b1cb729eb69`
- Superseded pre-run freeze: SHA-256 `210942a639571c235fcc932f4f7a97d32b8f8130d6090cf2d653d62b1ea1c386` on the earlier 2d5e42c2d8b9076e3b1b5f9c26cffd722f7e52aa base; main advanced before any invocation. The refreeze is prospective; no prior candidate, auditor, container or retry count changed. The earlier freeze is preserved in Git history.
- Candidate invocations: 0; auditor invocations: 0; formal container invocations: 0; retries: 0.
- Candidate output and auditor output paths on the dedicated OrbStack VM: absent at preregistration.
- Construction contract tests: 6/6 passed locally before formal freeze. This is fixture-development evidence only.
- Human responses: 0; independent reviewer signoffs: 0/not allocated.
- A01 `STOP_CONTAINER_SOURCE_MOUNT_EMPTY` and A02 `HOLD_ALLOCATION_ID_MISMATCH` remain preserved in their separate packages and are not repaired, pooled, or rerun here.

Formal candidate/auditor receipts and output hashes will be appended after the single allowed execution. A candidate or auditor failure is terminal; do not retry or replace the allocation.
