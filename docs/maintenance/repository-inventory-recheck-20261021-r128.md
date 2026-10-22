# Repository membership recheck r128 — 2026-10-21

Captured at 2026-10-20 18:07 UTC against main `f3cb822ecdc08e5425de55cbe712203e11b1293e`, after cleanup-plan PR #9310 merged. Main was read before and after complete GitHub CLI pagination and remained unchanged. IDs were sorted numerically; hashes are SHA-256 over LF-joined decimal IDs with no trailing LF.

| Set | Current rows | Sorted-ID SHA-256 | Difference from r126 |
|---|---:|---|---|
| Open Issues | 1,655 | `55f256c70aa9ea3dadf0bb7ae2b6477a863797ce6c27d2eea66b9b697ab2de64` | None |
| Open PRs | 463 | `3c1290839220a5c5274f3ca638aad310efa484b0eaa11dcf092d8c29931ca676` | None |

Commands: `gh issue list --repo Unjuno/agent-interface --state open --limit 5000 --json number` and `gh pr list --repo Unjuno/agent-interface --state open --limit 5000 --json number`; both returned complete sets. PR #9310 merged as `f3cb822ecdc08e5425de55cbe712203e11b1293e`, returning the PR set to the r126 membership. Its pre-merge state is separately preserved in [r127](repository-inventory-recheck-20261021-r127.md). No row metadata was duplicated; reuse r120 and refresh touched live records before state changes.

This is a membership-only recheck, not semantic disposition, PR readiness, ownership, or branch/worktree/raw-evidence custody.
