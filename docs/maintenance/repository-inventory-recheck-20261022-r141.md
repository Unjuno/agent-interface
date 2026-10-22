# Repository membership recheck r141 — after PR #8824

Captured 2026-10-22 03:01 UTC. The complete paginated GitHub API reads used 22 pages of open Issues and 5 pages of open PRs. The main SHA matched before and after: `d56609f46aae0be91d593a111adca84fca5a2893`.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` |
| Open PRs | 454 | `1c08fededaec68e78cb2738c9a620035cd93e34032e5448cbe713ed52b2fb988` |

Exact ID sets: [Issues](open-issue-ids-20261022-r141.csv), [PRs](open-pr-ids-20261022-r141.csv). Hashes are SHA-256 over numerically sorted decimal IDs joined by LF without a trailing LF.

Compared with r140, the open Issue set is unchanged. PR additions/removals: 0/1. Removed #8824 after merge. No other membership difference was observed.

Membership is not semantic disposition, ownership, exact-head readiness, evidence custody, or merge authorization. Refresh every touched record before changing state. No Issue or PR state changed during this snapshot, and no allocation was used.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh api --paginate --slurp 'repos/Unjuno/agent-interface/issues?state=open&per_page=100'`; `gh api --paginate --slurp 'repos/Unjuno/agent-interface/pulls?state=open&per_page=100'`.
