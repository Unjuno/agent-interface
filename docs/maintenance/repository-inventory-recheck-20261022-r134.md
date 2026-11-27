# Repository membership recheck r134 — after PR #9332

Captured at `2026-10-21 20:52:26 UTC` (`2026-10-22 05:52 JST`) against main
`410eb938bfb1f3cd4658e3136dded5d14eabd7c3`. Main was read before and after
complete GitHub CLI reads and remained stable. `gh issue list --state open`
and `gh pr list --state open` used limits of 5,000 and 3,000, respectively,
above the returned row counts.

| Set | Rows | SHA-256 of sorted decimal IDs joined by LF, no trailing LF | Difference from r133 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 462 | `650903dcf7919ee7979d04ea773c2354ae07e133396a79b1077a5280f743a34e` | None |

The exact Issue and PR ID sets match r133 despite the main update from
`0017149b7a0611b8a1d98160644a953911a858eb` to `410eb938bfb1f3cd4658e3136dded5d14eabd7c3`
through PR #9332. This is a membership snapshot only. It does not establish
semantic disposition, ownership, PR readiness, or artifact custody. Refresh
any selected live record before changing its state.
