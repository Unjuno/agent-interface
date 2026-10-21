# Repository open-work metadata refresh r85 — 2026-10-19

Captured during 2026-10-19 09:22–09:25 UTC from pagination-complete `gh issue list` and `gh pr list` reads for `Unjuno/agent-interface`. GitHub's default branch resolved to `main`; the SHA was the same before and after the listing window: `b1bff75ffa5d06f6d2c7d10bc7a89b1ab2dbdc16`.

Source and repeatable read: GitHub CLI `gh` 2.102.0. The exact paginated reads were:

```powershell
gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,state,labels,assignees,author,createdAt,updatedAt,url
gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number,title,state,isDraft,labels,assignees,author,createdAt,updatedAt,url,headRefName,headRefOid,baseRefName,baseRefOid,mergeStateStatus,reviewDecision,reviewRequests,statusCheckRollup
```

Both CLI reads completed below the 5,000-row limit. CSV exports are sorted numerically by ID; timestamps are UTC ISO 8601. The raw CLI JSON was used for conversion and was not committed; the row-level CSVs and hashes below are the preserved baseline.
| Surface | Open count | Membership vs. r70 | Detailed metadata |
|---|---:|---|---|
| Issues | 1,673 | unchanged | [Issue CSV](open-issues-20261019-r85.csv) |
| Pull requests | 482 | #9171 added; 8 no longer open | [PR CSV](open-prs-20261019-r85.csv) |

The eight PRs no longer open were #8825, #8803, #8798, #8795, #8794, #8793, and #8788 (merged), plus #8811 (closed without merge). These are observed transitions only; no Issue disposition is inferred from them. The 481 PR IDs common with r70 have unchanged head branch and head SHA. r70 did not record base SHA, so base changes cannot be compared with that snapshot.

Validation: pagination returned 1,673 issue rows and 482 PR rows; all row IDs were unique. Issue-ID SHA-256: `4ca4576b8a328d9f41b862a3c7ad3793edd9ddd085bb127d708796e9b6082dd6`. PR-ID SHA-256: `4371595095ac850d5fc20b408af138310b4805a5cb79ecc91fd79fd15e05a8c1`. The PR export contains current head/base names and SHAs, author, assignees, labels, draft state, review requests/decision, merge state, and raw status-check rollups. It records 1,864 check-run/context entries across 482 PRs; 31 PRs had no check rollup, and 38 had at least one `FAILURE` or `CANCELLED` conclusion. A failed/cancelled context is not by itself a merge decision; inspect required checks, current exact head/base, and local verification before each disposition.

CSV SHA-256:

- Issues: `0c95d010ada064fb79901a9e003f5ca6efba362759b72352ac811958bfc1d02f`
- Pull requests: `7bb012949493088a74a4df6943e3127fa3ea7be9f122fd316bb13f712b0c7dc9`

This refresh establishes current membership and PR metadata, not semantic triage, ownership, or merge readiness. It does not close Issues or PRs. See the [local repository surface and custody snapshot](repository-surface-map-20261019.md) for the separate worktree/ref/artifact audit.
