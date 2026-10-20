# Git worktree status census r03 — 2026-10-20

Captured at `2026-10-20 08:20 UTC` from the repository at main
`083e59c0abe71a0a693e231e08a14d6718df7ade`. Method: enumerate
`git worktree list --porcelain`, then run
`git status --porcelain --untracked-files=normal` once in each registered root.

| Registered worktrees | Clean in normal status | Dirty | Locked | Prunable |
|---:|---:|---:|---:|---:|
| 33 | 23 | 10 | 0 | 0 |

Dirty roots and status-entry counts:

| Worktree | Entries |
|---|---:|
| `agent-interface` | 24 |
| `mindustry-current-main-audit-20261005` | 2 |
| `pr8842-evidence-r01` | 1 |
| `repo-cleanup-r71-20261019` | 1 |
| `repository-consolidation-20261019` | 6 |
| `repository-consolidation-current-20261019` | 1 |
| `repository-inventory-r20-20261019` | 9 |
| `standard-caller-blocked-x11-a04-20261019` | 1 |
| `stdio-cancel-output-backpressure-20261020` | 2 |
| `x11-proxy-fake-relay-20261019` | 3 |

This local Git status census does not inspect ignored files, active processes,
worker/session owners, PR/base dependencies, or recoverability of untracked
outputs. No worktree was moved, pruned, reset, archived, or deleted. Preserve
all dirty roots until individual custody checks are complete.
