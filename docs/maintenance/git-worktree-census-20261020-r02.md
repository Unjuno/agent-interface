# Git worktree status recheck r02 — 2026-10-20

Captured at `2026-10-20 08:04 UTC` from the repository at main
`b368447275924d20fbd6a10b1a6de229bc94ee47`.
Method: enumerate `git worktree list --porcelain`, then run
`git status --porcelain --untracked-files=normal` once in each registered root.

| Registered worktrees | Clean in normal status | Dirty | Locked | Prunable |
|---:|---:|---:|---:|---:|
| 33 | 22 | 11 | 0 | 0 |

Dirty roots and status-entry counts:

| Worktree | Entries |
|---|---:|
| `agent-interface` | 24 |
| `mindustry-current-main-audit-20261005` | 2 |
| `pr8842-evidence-r01` | 1 |
| `repo-cleanup-governance-20261020` | 2 |
| `repo-cleanup-r71-20261019` | 1 |
| `repository-consolidation-20261019` | 6 |
| `repository-consolidation-current-20261019` | 1 |
| `repository-inventory-r20-20261019` | 9 |
| `standard-caller-blocked-x11-a04-20261019` | 1 |
| `stdio-cancel-output-backpressure-20261020` | 2 |
| `x11-proxy-fake-relay-20261019` | 3 |

This is a local Git status census only. It does not inspect ignored files,
running processes, worker/session owners, PR/base dependencies, or whether
untracked outputs have a verified recovery path. No worktree was moved,
pruned, reset, archived, or deleted. Preserve all ten dirty roots until those
custody checks are complete; a clean status alone is not deletion authority.
