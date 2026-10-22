# Repository open-work inventory r97 — 2026-10-19

Captured at 2026-10-19 16:00 UTC from paginated GitHub CLI listings for `Unjuno/agent-interface` at main `4ef4169b28952ff9b546cb1ab19aed74bb5efce0`. The default-branch SHA was `4ef4169b28952ff9b546cb1ab19aed74bb5efce0` before retrieval (15:58 UTC) and after retrieval (16:00 UTC). CLI row counts match GraphQL totals.

| Surface | Open count | CSV SHA-256 |
|---|---:|---|
| Issues | 1,673 | `D8C49919FF2F7BB19AB54B061F640341848AE48CA842D4048252A1E99E06A6CC` |
| Pull requests | 479 | `21F07AA428E0272E53CED4E2FCA007C9E67040854DFF54F2F2A3BEE4665126C5` |

Full rows: [open Issues CSV](open-issues-20261019-r97.csv) and [open PRs CSV](open-prs-20261019-r97.csv). Issue and PR membership is identical to r96; every open PR's recorded head/base names and OIDs are also unchanged. Updated timestamps and selected metadata were refreshed. This is a current membership and selected-metadata snapshot only: it does not semantically classify Issues, inspect every PR diff, establish owner/worktree custody, or authorize a state change. Re-fetch the affected item and owner/custody immediately before disposition.

Reproduction: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,labels,assignees`. GraphQL cross-check: `repository { issues(states:OPEN) { totalCount } pullRequests(states:OPEN) { totalCount } defaultBranchRef { target { oid } } }`.
