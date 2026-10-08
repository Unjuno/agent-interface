# Allocation STOP-01 — Issue #3809

**Disposition:** `STOP_SOURCE_OR_FREEZE_MISMATCH`  
**Allocation:** `issue3711-downstream-truncation-audit-v3-02`  
**Actions run:** [35535415702](https://github.com/Unjuno/agent-interface/actions/runs/35535415702)  
**Workflow/audit source commit:** `0ef8687b74d5a5c5583a82906a58d4bd41843070`  
**Frozen predecessor input commit:** `8bac49525c93835a69b6d441740a1c424faaecb2`

The GitHub-hosted Ubuntu 24.04 ARM64 job ran Docker Engine with the pinned Python 3.12 linux/arm64 image and `--network none`. Both fail-closed construction tests passed (2/2). The auditor then stopped before baseline or mutations with two metadata errors:

- `FROZEN_PLAN_HASH_MISMATCH`
- `FROZEN_AUDITOR_HASH_MISMATCH`

Inspection of the immutable audit freeze shows its source hash keys are full repository paths, not `PLAN.md` / `audit.py` basenames. The original freeze stores:

- `research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/PLAN.md` → `79741322f5c4b43d7d6a5a7b847bf3505bf94d2bc2f486ff27e40592515dd795`
- `research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/audit.py` → `ca3ccf5191d876eeda824555589c4580537dc04ec771fc52ef8914300ec289be`

The ten downloaded bytes all matched the corrected manifest before this run; the failure was in the auditor's freeze-key lookup. Result stdout is preserved verbatim in the adjacent file. Baseline is null and mutations are empty, as required by the fail-closed gate.

One audit container invocation occurred; zero formal experiment invocations occurred. This allocation is consumed and must not be retried. A corrected metadata mapping requires a fresh successor allocation.
