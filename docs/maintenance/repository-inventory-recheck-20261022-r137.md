# Repository membership recheck r137 — current-main refresh

Captured 2026-10-22 00:48:30 UTC against stable main `640501bbf1b2e96c488a7adf5dd453beea671e3a`. Complete open Issue and PR IDs were fetched with GitHub CLI `--limit 5000`; main SHA matched before and after.

| Set | Rows | Sorted-ID SHA-256 |
|---|---:|---|
| Open Issues | 1655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` |
| Open PRs | 458 | `d2a4ed942cb23e7e481ef9790762f3b0a3ad99163af62665e528acd7add90053` |

Exact IDs: [open Issue IDs](open-issue-ids-20261022-r137.csv) and [open PR IDs](open-pr-ids-20261022-r137.csv). Hash input is decimal IDs sorted numerically and joined by LF with no trailing LF.

Reusable row metadata captured during the same stable-main interval: [open Issues](open-issues-20261022-r137.csv) and [open PRs](open-prs-20261022-r137.csv). The metadata files contain the full captured membership; the ID-only files are the canonical hash input.

Prior complete r136 was captured against main `3e46261966957f0852703ededb4b6fb2f3a594bf` (1,655 Issues, 460 PRs). This receipt records membership only; it does not establish semantic disposition, owner, exact-head readiness, checks, evidence custody, or merge authorization. Re-fetch each record before state change.

Compared with r136, the exact Issue set is unchanged. The PR set is r136 minus #7290 and #8371: #7290 closed as superseded at 2026-10-21 23:19:54 UTC, and #8371 merged at 23:18:45 UTC. PR #9355 opened and merged at 2026-10-22 00:42:52 UTC, so it has no net membership effect. The exact ID CSVs above are the current full sets.

Commands: `gh api repos/Unjuno/agent-interface/git/ref/heads/main --jq .object.sha`; `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`.
