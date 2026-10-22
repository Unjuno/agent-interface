# Repository membership recheck r129 — 2026-10-22 JST

Captured at `2026-10-21 15:48:09 UTC` (2026-10-22 JST) against main
`9bf7ec15ea78eccd752adee1af8d00dc9545eaa0`. The main SHA read before and after
complete `gh issue list` / `gh pr list` pagination was identical. Both commands
used `--limit 5000` and returned all open records (1,655 Issues and 463 PRs).
The numeric IDs were sorted and SHA-256 hashed over LF-joined decimal IDs with
no trailing LF.

| Set | Rows | Sorted-ID SHA-256 | Change from r128 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None; exact set also matches r120 |
| Open PRs | 463 | `8f8016d67a4bae770f3ec8dc9823cbb5f75f6c9191fab97da026585d6dad3cd3` | Added #9315 and #9316; removed #8354 and #7188 |

Compared with the complete row-level r120 snapshot, Issues have no membership
delta. The open PR set added #9315 and #9316 and removed #8354, #7188, #8716,
#8733, #8841, and #8844. This is consistent with r128's recorded removal of
#8716, #8733, #8841, and #8844, followed by the two additions and two removals
shown above. Reuse r120's row metadata; fetch each touched live record before a
state change.

Commands:

```powershell
gh api repos/Unjuno/agent-interface/commits/main --jq .sha
gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number
gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number
```

This is a membership-only receipt. It does not classify meaning, assign
ownership, establish exact-head readiness, or resolve branch/worktree/raw-data
custody. PR #9316 was open and Draft at capture; the PR membership includes the
current plan PR.
