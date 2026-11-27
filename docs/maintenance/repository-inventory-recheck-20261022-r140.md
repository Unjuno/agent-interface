# Repository membership recheck r140 — after PR #9363

Captured 2026-10-22 02:56 UTC. The complete paginated GitHub API reads used 22 pages of open Issues and 5 pages of open PRs. The main SHA matched before and after: `930980a8daacf03f6e8a764105cd4d346308236c`.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` |
| Open PRs | 455 | `ddf9922a4955f7ac632302004bf9631d9475b4ebe0eba04d2c7e11d6cc2f459e` |

Exact ID sets: [Issues](open-issue-ids-20261022-r140.csv), [PRs](open-pr-ids-20261022-r140.csv). Hashes are SHA-256 over numerically sorted decimal IDs joined by LF without a trailing LF.

Compared with r139, the open Issue set is unchanged. PR additions/removals: 0/1. Removed #9363 after it merged at this main SHA. No other membership difference was observed.

Issue #17, #57, and #7924 were read live at capture time and remain open. #7924's STOP/HOLD is unchanged; this count snapshot does not grant a WSLc/Docker allocation.

Membership is not semantic disposition, ownership, exact-head readiness, evidence custody, or merge authorization. Refresh every touched record before changing state. No Issue or PR was changed during this snapshot, and no allocation was used.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh api --paginate --slurp 'repos/Unjuno/agent-interface/issues?state=open&per_page=100'`; `gh api --paginate --slurp 'repos/Unjuno/agent-interface/pulls?state=open&per_page=100'`.
