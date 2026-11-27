# Repository membership recheck r135 — after #9315 closure and PR #9334

Captured at `2026-10-21 21:00:41 UTC` (`2026-10-22 06:00 JST`) against main
`0e289460404b626e3cc26eec4be0b0170bd60ee0`. Main was read before and after
complete GitHub CLI reads and remained stable. `gh issue list --state open`
and `gh pr list --state open` used limits of 5,000 and 3,000, respectively,
above the returned row counts.

| Set | Rows | SHA-256 of sorted decimal IDs joined by LF, no trailing LF | Difference from r134 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 461 | `0aca0c5e759e50d1623c338f01540ff51f9ac1fe6ff06861fa933ab66ae9a7f1` | Set changed; r134 recorded 462 |

The Issue set is unchanged. The open PR count fell by one after the superseded
Draft PR #9315 was closed; cleanup documentation PRs #9333 and #9334 were
merged before this capture. This snapshot establishes membership only, not
semantic disposition, active ownership, merge readiness, or artifact custody.
Refresh each selected live record before changing its state.
