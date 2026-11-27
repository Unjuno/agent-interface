# Repository membership recheck r131 — after PR #9323

Captured at `2026-10-21 19:51 UTC` (`2026-10-22 JST`) against main
`7795eda5bed22d1029bbc5dbf0afe2e0a18291fc`. The remote main SHA was read before
and after both complete GitHub CLI reads and remained stable. Commands used
`--limit 5000`; IDs were sorted numerically and hashed as LF-joined decimal
IDs with no trailing LF.

| Set | Rows | Sorted-ID SHA-256 | Difference from full r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 462 | `650903dcf7919ee7979d04ea773c2354ae07e133396a79b1077a5280f743a34e` | Added #9315; #7188, #8354, #8716, #8733, #8841, and #8844 absent |

The sorted Issue and PR sets are byte-for-byte membership-equivalent to r130.
This corrects r130's stated change from r129: the actual newly open PR was
#9315, not a removal of #9316. PR #9316 was created and merged between the
r129 and r130 snapshots and therefore was not an open-set member at either
snapshot. The totals and hashes alone establish membership only, not semantic
disposition, PR readiness, ownership, or evidence custody. Refresh each live
record before a state change.
