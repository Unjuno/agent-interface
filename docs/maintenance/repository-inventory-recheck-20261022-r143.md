# Repository membership recheck r143 — after PR #9367 and scoped closure of #8493

Captured 2026-10-22 03:09:00 UTC against `main` `8f43c02c013aa77c74d495bd48cc72a7627bf081`. Complete paginated GitHub CLI reads finished with the same main SHA before and after.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1654 | `f72384f45b9f90d5e8f9e68927f98320c3398641716f8b58f69525ccc58ece21` |
| Open PRs | 453 | `17b5b07e90a662f1feb42d730673c6d1bb90eee7453c27e98e308a34fb8170d1` |

Exact ID sets: [Issues](open-issue-ids-20261022-r143.csv), [PRs](open-pr-ids-20261022-r143.csv). IDs are sorted numerically. Hashes are SHA-256 over decimal IDs joined by LF without a trailing LF.

Compared with r142, Issue #8493 is the only Issue removed. The open PR set and sorted-ID hash are unchanged. The successful full-list reads returned 1,654 Issues and 453 PRs, below the CLI limit of 5,000. Counts do not establish semantic disposition, assignment, review readiness, or custody.

This is a complete membership baseline only. Refresh a touched record before further state changes. No allocation or container operation was used.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`.