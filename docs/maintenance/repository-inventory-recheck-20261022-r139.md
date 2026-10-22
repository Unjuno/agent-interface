# Repository membership recheck r139 — after PR #8833

Captured 2026-10-22 02:48 UTC. The complete paginated GitHub API reads used 22 pages of open Issues and 5 pages of open PRs. The main SHA matched before and after: `2b29ebe0ca6fe8214985a7e50c46a72f5f3af17f`.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` |
| Open PRs | 456 | `9609c3ecca35f96fb569995a2b074f7a09b2de6dd6c72791b5c251a9b5de3723` |

Exact ID sets: [Issues](open-issue-ids-20261022-r139.csv), [PRs](open-pr-ids-20261022-r139.csv). Hashes are SHA-256 over numerically sorted decimal IDs joined by LF without a trailing LF.

Compared with r138, the open Issue set is unchanged. PR additions/removals: 1/2. Added #9363. Removed #7120 and #8833. Live reads confirm #7120 is closed as superseded, #8833 merged at this main SHA, and #9363 is open, non-draft, mergeable, with both reported checks passing. These facts do not establish #9363's design/evidence disposition or authorize its merge.

Issue #17, #57, and #7924 were read live at capture time and remain open. #7924's current body/ownership evidence was not re-audited here; this count snapshot does not alter its STOP/HOLD.

Membership is not semantic disposition, ownership, exact-head readiness, evidence custody, or merge authorization. Refresh every touched record before changing state. This recheck did not close or merge any Issue or PR and did not use WSLc/Docker.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`; `gh api --paginate --slurp 'repos/Unjuno/agent-interface/issues?state=open&per_page=100'`; `gh api --paginate --slurp 'repos/Unjuno/agent-interface/pulls?state=open&per_page=100'`.
