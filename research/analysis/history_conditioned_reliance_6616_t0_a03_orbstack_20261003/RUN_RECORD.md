# Issue #6616 A03 run record

## Frozen pre-run state

- Allocation: `history-conditioned-reliance-6616-t0-a03-20261003`
- Base main after current-main refreeze: `5e9d5b3e8d1f5685ccd71fc1ebb50b1cb729eb69`
- Superseded pre-run freeze: SHA-256 `210942a639571c235fcc932f4f7a97d32b8f8130d6090cf2d653d62b1ea1c386` on the earlier 2d5e42c2d8b9076e3b1b5f9c26cffd722f7e52aa base; main advanced before any invocation. The refreeze is prospective; no prior candidate, auditor, container or retry count changed. The earlier freeze is preserved in Git history.
- Candidate invocations: 0; auditor invocations: 0; formal container invocations: 0; retries: 0.
- Candidate output and auditor output paths on the dedicated OrbStack VM: absent at preregistration.
- Pre-run command audit caught that a shared source bind mount would make `oracle.json` visible to the candidate despite the candidate not opening it. Before any invocation, commands were corrected to disjoint mounts (`src-candidate` excludes oracle/auditor; `src-audit` is mounted only into auditor). The initial preregistration freeze is preserved in Git history and superseded prospectively; Issue addendum records the source-visibility correction.
- The initial preregistration freeze SHA-256 `1e07b1b8f7b6037cbb2c3b314a5867e9587779eaa16a3bdf9839a221aa2f1012` is superseded before execution by the corrected mount freeze. No invocation counters changed.
- A final audit-source preflight found its independent hash verifier also reads `candidate.py`. Added that code to the auditor-only source mount (still not visible to candidate), superseding the immediately previous pre-run freeze SHA-256 `192004ca1e80cbf96434208e7758ba703dab97feb112225468c43f9e2f4c598c`. No invocation counters changed.
- Construction contract tests: 6/6 passed locally before formal freeze. This is fixture-development evidence only.
- Human responses: 0; independent reviewer signoffs: 0/not allocated.
- A01 `STOP_CONTAINER_SOURCE_MOUNT_EMPTY` and A02 `HOLD_ALLOCATION_ID_MISMATCH` remain preserved in their separate packages and are not repaired, pooled, or rerun here.

Formal candidate/auditor receipts and output hashes will be appended after the single allowed execution. A candidate or auditor failure is terminal; do not retry or replace the allocation.
