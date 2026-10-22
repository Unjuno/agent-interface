# Repository membership recheck r145 — after PR #9369

Captured 2026-10-22 03:18:17 UTC against `main` `1a21bef00c431af02fa7f280c7589b48d03402af`. Complete open Issue and PR reads finished with the same main SHA before and after.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1654 | `f72384f45b9f90d5e8f9e68927f98320c3398641716f8b58f69525ccc58ece21` |
| Open PRs | 453 | `17b5b07e90a662f1feb42d730673c6d1bb90eee7453c27e98e308a34fb8170d1` |

Exact ID sets: [Issues](open-issue-ids-20261022-r145.csv), [PRs](open-pr-ids-20261022-r145.csv). IDs are numerically sorted; hashes are SHA-256 over decimal IDs joined by LF without a trailing LF. Each full read returned below the 5,000-row command limit. Compared with r144, no membership changes were observed; PR #9369 opened and merged without net membership effect.

Membership is not semantic disposition, ownership, readiness, or custody. No WSLc allocation or container operation was used.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`.