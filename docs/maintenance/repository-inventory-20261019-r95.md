# Repository open-work inventory r95 — 2026-10-19

Captured at 2026-10-19 14:37:58 UTC from paginated GitHub CLI listings for `Unjuno/agent-interface` at main `97f3d3625c716631858d9eed685c581c7e5aa5fc`. The CLI result counts match GraphQL.

| Surface | Open count | CSV SHA-256 |
|---|---:|---|
| Issues | 1673 | `3BB1D84C57AEA2FF2605CA13FF4AD74B87744C6C730197319B2B73E35B72DE89` |
| Pull requests | 479 | `B44F3734273E62016F47752668B0C87D7DCD00E6846EDD0B0AC0648F1F934E9C` |

Full rows: [open Issues CSV](open-issues-20261019-r95.csv) and [open PRs CSV](open-prs-20261019-r95.csv). The main SHA was rechecked after pagination and remained `97f3d3625c716631858d9eed685c581c7e5aa5fc`. Compared with r88, the Issue ID set is unchanged and the only PR removed from the open set is #9194, verified merged at this main commit. This is membership/metadata only; it does not semantically classify rows, establish current ownership, review diffs, or authorize state changes. Re-fetch the affected Issue/PR and owner/custody immediately before disposition.

Reproduction: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,mergeable,labels,assignees`. Both CLI counts matched GraphQL.
