# Repository membership recheck r132 — after PR #9329

Captured at `2026-10-21 20:35:11 UTC` (`2026-10-22 05:35 JST`) against main
`d0f392e55db5f53c17592ae08360cc5e45940b25`. The main ref was read before and
after complete GitHub CLI reads and remained stable. `gh issue list` and
`gh pr list` were run with `--state open` and limits of 5,000 and 3,000,
respectively, above the returned row counts. The new open PR #9330 is included
in this snapshot; it is this documentation update's PR.

| Set | Rows | SHA-256 of sorted decimal IDs joined by LF, no trailing LF | Difference from r131 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None; matches full r120 and r131 |
| Open PRs | 463 | `1f14e06ae079ef6f4bb69006d6e4b6f8343d0cdfd8776b7cd1d8c177726956a0` | Added #9330; no removals |

Compared with the full r120 PR metadata, the current set adds #9315 and #9330
and no longer contains #7188, #8354, #8716, #8733, #8841, or #8844. Thus r132
is r131 plus the newly opened #9330. The exact set comparison was computed
against the full r120 JSON; r131 states that its set was membership-equivalent
to that same baseline. This is a membership snapshot only: it does not classify
Issue meaning, active ownership, PR readiness, or evidence custody. Refresh any
touched live record before a state change.
