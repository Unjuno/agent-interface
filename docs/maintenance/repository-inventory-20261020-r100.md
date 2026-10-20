# Repository open-work inventory r100 — 2026-10-20

Captured at 2026-10-20 05:26:15 UTC for `Unjuno/agent-interface` at main `282a05b02d8d48053c88bcdb08ace54694068a6a`. Paginated CLI listings were bracketed by GraphQL reads; main remained fixed and CLI counts matched GraphQL.

| Surface | Open count | CSV SHA-256 |
|---|---:|---|
| Issues | 1,672 | `fa90be1f4ae97d789dc99f43653ce58bb40bbdf4918af4d96e3dc171cc417dde` |
| Pull requests | 476 | `1648854bf9bf429fb33807b01752aac58b7b12c06219cbbc1026244e985b58f0` |

Full rows: [open Issues CSV](open-issues-20261020-r100.csv) and [open PRs CSV](open-prs-20261020-r100.csv). Compared with r99, PR #9224 was added and PR #8832 left the open set; Issue membership is unchanged. PR #8843 had already left the set before r99. #8832 was closed as a duplicate after merged #9217 preserved the same frozen T0 evidence, fixed the portable test fixture, and passed focused tests. #8843 was superseded by merged #9218 before r99 was captured. This is membership and selected metadata, not a semantic review of every Issue/PR or proof of worktree custody. Refresh exact records before further state changes.

Reproduction: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,labels,assignees`. GraphQL cross-check: `repository { issues(states:OPEN) { totalCount } pullRequests(states:OPEN) { totalCount } defaultBranchRef { target { oid } } }`.
