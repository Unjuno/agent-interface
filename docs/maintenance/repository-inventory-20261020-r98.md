# Repository open-work inventory r98 — 2026-10-20

Captured at 2026-10-20 04:21:59 UTC from paginated GitHub CLI listings for `Unjuno/agent-interface` at main `5bdef852869d8a3a1c2de792221fadd0db199586`. GraphQL was read before and after both listings; the default-branch SHA remained unchanged. CLI counts match GraphQL totals.

| Surface | Open count | CSV SHA-256 |
|---|---:|---|
| Issues | 1,673 | `a0527e0caaedca7ada487cd63618aebf785cefbfe0098645f0747154a00ed686` |
| Pull requests | 477 | `3ccb62a075a99fbe4e1ebd331a5798d03b475338b39acb4832b149f6b0fdb7f0` |

Full rows: [open Issues CSV](open-issues-20261020-r98.csv) and [open PRs CSV](open-prs-20261020-r98.csv). Issue membership is unchanged from r97. Compared with r97, the open PR set has no additions and no longer includes #8772 and #8842. Titles, updated times, labels, assignees, PR head/base refs, draft state and review decision were refreshed. This is membership and selected metadata only; it is not semantic triage, full-diff review, owner/worktree proof, or authorization to change state. Refresh each exact record before disposition.

The associated [worker packet map](parallel-worker-packets-20261020-r01.md) turns selected live records into independent, bounded, read-only review tasks. It preserves research Issues and unresolved custody rather than using a zero-count target.

Reproduction: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,labels,assignees`. GraphQL cross-check: `repository { issues(states:OPEN) { totalCount } pullRequests(states:OPEN) { totalCount } defaultBranchRef { target { oid } } }`.
