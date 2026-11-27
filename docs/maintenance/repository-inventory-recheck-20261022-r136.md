# Repository membership recheck r136 — after #7181 and #9346

Captured during `2026-10-21 23:06:35–23:06:50 UTC` against remote `main`
`3e46261966957f0852703ededb4b6fb2f3a594bf`. The main ref was read before and
after complete GitHub CLI reads and stayed stable. Both commands used `--limit
5000`, above the returned row counts. IDs were sorted numerically; hashes are
SHA-256 over decimal IDs joined by LF without a trailing LF.

| Set | Rows | Sorted-ID SHA-256 | Difference |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | Same exact set as r135 and full metadata r120 |
| Open PRs | 460 | `7adc97881d121d21876782e3f56b842079b1053a24696ab8a8b0bef3b62651a3` | Compared with r120: no additions; #7181 and six previously removed IDs are absent |

The prior r135 set was r120 minus #7188, #8354, #8716, #8733, #8841 and
#8844. The only additional r120 PR absent at this capture is #7181, which merged
at `a341ea8b2ed76d846e626076066cb563d804c716`. PR #9346 was opened and merged
between these captures at `4fd2fe76b516844c89efc2e3fb044dff6ceec5bc`; it is not
in the current open set. The complete current PR ID list exactly matches r120
minus the seven IDs named above. The Issue ID set remains unchanged.

Commands:

```text
gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number
gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number
```

This is a membership snapshot, not semantic triage, ownership, PR readiness,
or evidence custody. Refresh each live record before changing its state.
