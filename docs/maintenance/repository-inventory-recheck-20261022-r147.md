# Repository membership recheck r147 — after PR #9378

Captured 2026-10-22 against `main` `b481ce7e5950352ac39cde1612f9ef691d541c4c`.
Complete open Issue and PR reads finished with the same main SHA before and
after.

| Set | Rows | Sorted-ID SHA-256 | Comparison |
|---|---:|---|---|
| Open Issues | 1,654 | `f72384f45b9f90d5e8f9e68927f98320c3398641716f8b58f69525ccc58ece21` | Exact ID sequence equals r145 |
| Open PRs | 453 | `17b5b07e90a662f1feb42d730673c6d1bb90eee7453c27e98e308a34fb8170d1` | Exact ID sequence equals r145 |

The r145 ID files are reused because the freshly paginated sets compare
row-for-row with them: [open Issues](open-issue-ids-20261022-r145.csv) and
[open PRs](open-pr-ids-20261022-r145.csv). Counts match the fetched row counts.
The Issue and PR membership is unchanged from r146 despite PRs #9377 and #9378
being opened and merged during the interval. Membership does not establish
semantic disposition, PR readiness, current ownership, or artifact custody.

Commands: `gh api repos/Unjuno/agent-interface/commits/main --jq .sha`,
`gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number`,
and `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`.
Before/after main SHA: `b481ce7e5950352ac39cde1612f9ef691d541c4c`.

No WSLc/Docker allocation or container operation was used.
