# Repository membership recheck r142 — after PR #8819

Captured 2026-10-22 03:06:59 UTC against `main` `7ee142d642de45c1129a138e01f3519ed4a1449c`. Complete paginated GitHub CLI reads finished with the same main SHA before and after.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` |
| Open PRs | 453 | `17b5b07e90a662f1feb42d730673c6d1bb90eee7453c27e98e308a34fb8170d1` |

Exact ID sets: [Issues](open-issue-ids-20261022-r142.csv), [PRs](open-pr-ids-20261022-r142.csv). IDs are sorted numerically. Hashes are SHA-256 over decimal IDs joined by LF without a trailing LF.

Compared with r141, the Issue set is unchanged. The PR set removed #8819 after it merged at this main SHA; no other membership change was observed. The successful full-list reads returned 1,655 Issues and 453 PRs, below the CLI limit of 5,000. Membership counts do not establish semantic disposition, assignment, review readiness, or custody.

This snapshot is a complete membership baseline only. Refresh a touched live record before any state change. No allocation or container operation was used.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`.