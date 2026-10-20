# Repository membership recheck r114 — 2026-10-20

Captured at 2026-10-20 10:39:08 UTC from complete paginated GitHub CLI lists for Unjuno/agent-interface. Main remained at `270e886685f3814f053824a5110e9226b1b3f5a5` before and after the read; CLI totals matched both bracketing GraphQL totals.

| Surface | Open count | SHA-256 of sorted numeric IDs (UTF-8, LF after each ID) | Full metadata |
|---|---:|---|---|
| Issues | 1672 | `073738bd5d54cc178a3f92d9df0d03d054a12968ccf5fd575ed57e8ee72e55d4` | [open Issues JSON](open-issues-20261020-r114.json) |
| Pull requests | 468 | `878a28d681a0ae705654b670693106498874c525afe2ca828aa129b3dccafb3a` | [open PRs JSON](open-prs-20261020-r114.json) |

Compared with r113, the full row-level sets can be compared by number; r113 remains immutable. This inventory records membership and selected metadata only. It does not establish semantic disposition, ownership, evidence custody, or merge/closure eligibility. Refresh the exact live item before any state change.

Reproduction: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author` and `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,labels,assignees`. Both list totals matched GraphQL before and after; main SHA was stable.