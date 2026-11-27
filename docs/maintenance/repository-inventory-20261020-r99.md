# Repository open-work inventory r99 — 2026-10-20

Captured at 2026-10-20 05:22:53 UTC for `Unjuno/agent-interface` at main `282a05b02d8d48053c88bcdb08ace54694068a6a`. The paginated GitHub CLI listings were bracketed by GraphQL reads; the default-branch SHA stayed fixed and CLI counts matched GraphQL.

| Surface | Open count | CSV SHA-256 |
|---|---:|---|
| Issues | 1,672 | `fa90be1f4ae97d789dc99f43653ce58bb40bbdf4918af4d96e3dc171cc417dde` |
| Pull requests | 476 | `9b67b9d1aeb39b5ba56c609b113eb2be8ba0677a10bc3df05dc2ff0eaceefa8e` |

Full rows: [open Issues CSV](open-issues-20261020-r99.csv) and [open PRs CSV](open-prs-20261020-r99.csv). Compared with r98, no items were added; Issue #8574 and PR #8843 left the open sets. Issue #8574's scoped T0 is preserved by merged #9217 and explicitly left broader transfer deferred. PR #8843 was superseded by merged #9218, which retains the package and repairs its manifest; the evidence remains construction-only. This inventory records membership and selected metadata only; it is not a review of every PR diff or proof of owner/worktree custody. Refresh exact records before any further action.

Reproduction: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,labels,assignees`. GraphQL cross-check: `repository { issues(states:OPEN) { totalCount } pullRequests(states:OPEN) { totalCount } defaultBranchRef { target { oid } } }`.
