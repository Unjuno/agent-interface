# Repository open-work inventory r101 — 2026-10-20

Captured at 2026-10-20 05:49:10 UTC for Unjuno/agent-interface at main $mainSha. Complete paginated GitHub CLI listings were bracketed by GraphQL reads; main remained fixed and CLI totals matched GraphQL.

| Surface | Open count | CSV SHA-256 |
|---|---:|---|
| Issues | 1672 | `fe042199a666aa88399cffbcd4560295acaebb9da12f3de1d3ee7205796c8bf0` |
| Pull requests | 475 | `c8d68d09d7c48e43e770e91699ca93c676c7088bb421164c8717cd2f88c4576c` |

Full rows: [open Issues CSV](open-issues-20261020-r101.csv) and [open PRs CSV](open-prs-20261020-r101.csv). This is current membership and selected metadata only; it does not classify meaning, ownership, evidence custody, or closure/merge eligibility. Refresh the exact live record before disposition.

Reproduction: gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author; gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,labels,assignees. GraphQL before/after confirmed main $mainSha, 1672 open Issues and 475 open PRs.

Compared with r100, Issue membership is unchanged and PR #9224 left the open set after merging at 2026-10-20 05:28:05 UTC (merge commit `4945b0310a5a27d59cb85e3c7ef7c49916f23b30`). No other ID additions or removals were found.
