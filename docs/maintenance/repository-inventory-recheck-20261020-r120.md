# Repository membership recheck r120 — 2026-10-20

Captured at 2026-10-20 14:32:53 UTC against GitHub main $(@{defaultBranchRef=; issues=; pullRequests=}.defaultBranchRef.target.oid). GraphQL object totals and the main OID were read before and after the complete paginated gh CLI reads and remained stable. CLI limits were 2,000 Issues and 1,000 PRs, both above the returned set sizes.

| Set | CLI rows | GraphQL before/after | SHA-256 of sorted newline-separated IDs |
|---|---:|---:|---|
| Open Issues | 1655 | 1655 / 1655 | `720d98407db3844e421e3e647bfec33889e90e842d1d3bd4b601c2db93a4faa9` |
| Open PRs | 467 | 467 / 467 | `d8994f91eb4d1a4619e2006bbec6cb67b89c25ccb94eb51021834aac9bd17992` |

Full row metadata: [open Issues](open-issues-20261020-r120.json) and [open PRs](open-prs-20261020-r120.json). This is a membership snapshot, not semantic classification, ownership, PR readiness, or worktree custody. Re-fetch exact items and dependencies before each state change.