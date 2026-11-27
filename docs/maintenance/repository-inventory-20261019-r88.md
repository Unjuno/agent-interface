# Repository open-work inventory r88 — 2026-10-19

Captured at 2026-10-19 14:02:03 UTC from fully paginated GitHub CLI listings for `Unjuno/agent-interface`; `main` remained `68a15ed1d50124390e3f88a85829db0f702bd1a8` before and after the read.

| Surface | Open count | Previous complete inventory | Note |
|---|---:|---|---|
| Issues | 1,673 | r87 | Membership and selected metadata only. |
| Pull requests | 480 | r87 | Includes exact head/base, draft and review metadata. |

Full rows: [open Issues CSV](open-issues-20261019-r88.csv) and [open PRs CSV](open-prs-20261019-r88.csv).

This inventory is a navigation snapshot, not semantic classification, proof of ownership, review of diffs, or authorization to close, merge, or delete anything. Re-fetch each live item, comments, exact head, evidence, current owner/worktree, and actual protections immediately before a disposition. A listing row is not a completed triage.

Reproduction:

```powershell
gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone
gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,isDraft,reviewDecision,mergeable,labels,assignees
```
