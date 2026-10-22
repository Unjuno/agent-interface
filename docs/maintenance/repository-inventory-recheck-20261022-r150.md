# Repository membership recheck r150 — after PR #9398

Captured 2026-10-22 against main `b57e140848087ab814db874f7dfe410926afd387`. Complete open Issue and PR membership reads were bracketed by the same remote main SHA.

| Set | Rows | Exact ID CSV | SHA-256 |
|---|---:|---|---|
| Open Issues | 1,654 | [IDs](open-issue-ids-20261022-r150.csv) | `8e2c08331f735f9d8bd004c715515886aa3a46ec77a0fc5c4e178e4b7c88aa59` |
| Open PRs | 452 | [IDs](open-pr-ids-20261022-r150.csv) | `2d938f6e72e337ac69ed6d5586576e762bb2b6741ea118a532f2a1ff46024c6d` |

The reads used `gh issue list --state open --limit 5000 --json number` and `gh pr list --state open --limit 5000 --json number`, sorted by numeric ID. The SHA-256 values cover the exact committed Git blob bytes (UTF-8 CSV with LF line endings). Compared with r149: Issues added none, removed none; PRs added none, removed none. PR #9398 was opened and merged between the two reads, so the exact open-ID set has no net change. These are membership deltas only and do not establish semantic disposition, ownership, custody or merge readiness. Refresh a live record before any state change.

PR #9398 merged at this main SHA. The full queue is still not semantically classified. Worktree custody remains unresolved; do not delete or archive based on this membership read. This recheck used no WSLc or Docker allocation.
