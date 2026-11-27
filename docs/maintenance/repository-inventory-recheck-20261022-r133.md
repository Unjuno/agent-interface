# Repository membership recheck r133 — after PR #9331

Captured at `2026-10-21 20:47:27 UTC` (`2026-10-22 05:47 JST`) against main
`0017149b7a0611b8a1d98160644a953911a858eb`. The main ref was read before and
after complete GitHub CLI reads and remained stable. `gh issue list` and
`gh pr list` were run with `--state open` and limits of 5,000 and 3,000,
respectively, above the returned row counts.

| Set | Rows | SHA-256 of sorted decimal IDs joined by LF, no trailing LF | Difference from r131 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 462 | `650903dcf7919ee7979d04ea773c2354ae07e133396a79b1077a5280f743a34e` | None |

The Issue and PR ID sets match r131 exactly. Compared with the full r120
metadata, the open PR set adds #9315 and no longer contains #7188, #8354,
#8716, #8733, #8841, or #8844. The temporary #9330 and #9331 documentation and
runtime PRs were both merged before this capture and are absent. This is a
membership snapshot only: it does not classify Issue meaning, active
ownership, PR readiness, or evidence custody. Refresh any touched live record
before a state change.
