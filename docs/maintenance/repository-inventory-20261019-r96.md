# Repository open-work inventory r96 — 2026-10-19

Captured at 2026-10-19 15:22 UTC from paginated GitHub CLI listings for `Unjuno/agent-interface` at main `b0e47dd4f67a57db5c530d19251ad172e29554d7`. The main SHA was read before the listings, matched the current `origin/main`, and matched the GitHub default-branch SHA after the listings. CLI counts match GraphQL totals.

| Surface | Open count | CSV SHA-256 |
|---|---:|---|
| Issues | 1,673 | `03993E70539D465ADC389DEB8010514B0AB137A7677B464FA9136C799FC562AD` |
| Pull requests | 479 | `F79C2E8E07B46FD334815E0970D13425C5C89C4DB6E9C4D39AE1B0FC4614DBA0` |

Full rows: [open Issues CSV](open-issues-20261019-r96.csv) and [open PRs CSV](open-prs-20261019-r96.csv). Both ID sets match r95; the refreshed PR rows include exact head/base OIDs, draft and review-decision fields. This is membership and selected metadata only. It does not semantically classify rows, establish current ownership, review every PR diff/check, or authorize state changes. Re-fetch the affected Issue/PR and owner/custody immediately before disposition.

Reproduction: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,labels,assignees,milestone,author`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,url,createdAt,updatedAt,author,headRefName,headRefOid,baseRefName,baseRefOid,isDraft,reviewDecision,labels,assignees`. GraphQL cross-check: `repository { issues(states:OPEN) { totalCount } pullRequests(states:OPEN) { totalCount } defaultBranchRef { target { oid } } }`.
