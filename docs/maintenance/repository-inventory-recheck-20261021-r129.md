# Repository membership recheck r129 — 2026-10-21

Captured at 2026-10-21 13:49 UTC against remote `main` `9bf7ec15ea78eccd752adee1af8d00dc9545eaa0`. The main ref was read before and after complete GitHub CLI reads and remained unchanged. Issue and PR IDs were sorted numerically; hashes are SHA-256 of LF-joined decimal IDs with no trailing LF.

| Set | Current rows | Sorted-ID SHA-256 | Difference from full r120 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 461 | `0aca0c5e759e50d1623c338f01540ff51f9ac1fe6ff06861fa933ab66ae9a7f1` | #7188, #8354, #8716, #8733, #8841, and #8844 absent; no additions |

Commands: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number` and `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; each returned the complete set. Issue membership exactly matches full r120. PR membership is exactly r120 minus the six IDs listed above. Reuse r120's row metadata for discovery, but refresh each live record and its linked evidence before any state change.

This is a membership recheck only. It does not establish semantic disposition, current PR readiness, ownership, or branch/worktree/raw-evidence custody. It makes no Issue or PR state change.
