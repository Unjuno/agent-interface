# Repository membership recheck r144 — after PR #9368

Captured 2026-10-22 03:13:06 UTC against `main` `178983ac3cb884f19536810ce56b53d79122090a`. Complete open Issue and PR reads finished with the same main SHA before and after.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1654 | `f72384f45b9f90d5e8f9e68927f98320c3398641716f8b58f69525ccc58ece21` |
| Open PRs | 453 | `17b5b07e90a662f1feb42d730673c6d1bb90eee7453c27e98e308a34fb8170d1` |

Exact ID sets: [Issues](open-issue-ids-20261022-r144.csv), [PRs](open-pr-ids-20261022-r144.csv). IDs are numerically sorted; hashes are SHA-256 over decimal IDs joined with LF and no trailing LF. The complete reads returned fewer than the 5,000-row command limit. This is membership only, not semantic disposition, ownership, readiness, or custody.

Compared with r143, no Issue or PR membership change was observed. PR #9368 opened and merged during this interval, so it had no net effect on the open PR set.

No WSLc allocation or container operation was used. Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`.