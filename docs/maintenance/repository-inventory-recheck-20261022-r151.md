# Repository membership recheck r151 — after PR #9399

Captured 2026-10-22 against main 08064035460187ba5c8c5cbb2f4e9732ca622ada. Complete open Issue and PR membership reads were bracketed by the same remote main SHA.

| Set | Rows | Exact ID CSV | SHA-256 |
|---|---:|---|---|
| Open Issues | 1,654 | [IDs](open-issue-ids-20261022-r151.csv) | 8e2c08331f735f9d8bd004c715515886aa3a46ec77a0fc5c4e178e4b7c88aa59 |
| Open PRs | 452 | [IDs](open-pr-ids-20261022-r151.csv) | 2d938f6e72e337ac69ed6d5586576e762bb2b6741ea118a532f2a1ff46024c6d |

The reads used gh issue list --state open --limit 5000 --json number and gh pr list --state open --limit 5000 --json number, sorted by numeric ID. The SHA-256 values cover the exact committed Git blob bytes (UTF-8 CSV with LF line endings). Compared with r150: Issues added none, removed none; PRs added none, removed none. PR #9399 was opened and merged between the reads, so the exact open-ID set has no net change. These are membership deltas only and do not establish semantic disposition, ownership, custody or merge readiness. Refresh a live record before any state change.

PR #9399 merged at this main SHA. The queue remains semantically unclassified. The linked-worktree custody discrepancy review is recorded in [the organization plan](../REPOSITORY_ORGANIZATION_PLAN.md). This recheck used no WSLc or Docker allocation.
