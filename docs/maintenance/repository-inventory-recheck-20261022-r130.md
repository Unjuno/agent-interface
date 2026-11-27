# Repository membership recheck r130 — after PR #9316

Captured at `2026-10-21 15:51:20 UTC` (2026-10-22 JST) against main
`976d36443548e02d169b0b44fab6877224464be4`, the squash merge of PR #9316. The
main SHA read before and after complete `gh issue list` / `gh pr list`
pagination was identical. Both commands used `--limit 5000` and returned all
open records. IDs were sorted numerically and SHA-256 hashed over LF-joined
decimal IDs with no trailing LF.

| Set | Rows | Sorted-ID SHA-256 | Change from r129 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 462 | `650903dcf7919ee7979d04ea773c2354ae07e133396a79b1077a5280f743a34e` | Removed merged PR #9316 |

No Issue changed membership. PR #9316 was the only PR membership change between
r129 and r130; #9315 remains open. This is a membership-only receipt, not
semantic disposition, merge readiness, ownership, or custody.
