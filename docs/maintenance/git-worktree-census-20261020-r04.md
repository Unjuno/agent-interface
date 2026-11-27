# Git worktree status census r04 — 2026-10-20

Captured at `2026-10-20 10:52 UTC` from the repository at main
`3f7eec087f37a02acd38299c5fe1173be4f36977`. Method: enumerate
`git worktree list --porcelain`, then run
`git status --porcelain=v1 --untracked-files=normal` once in each registered
root. The repository reported 37 roots; all paths existed, and Git reported 0
locked and 0 prunable roots.

| Registered worktrees | Existing | Clean in normal status | Dirty | Locked | Prunable |
|---:|---:|---:|---:|---:|---:|
| 37 | 37 | 26 | 11 | 0 | 0 |

Dirty roots and status-entry counts:

| Worktree | Entries |
|---|---:|
| `agent-interface` | 31 |
| `goal-computer-control-next-20261020` | 2 |
| `mindustry-current-main-audit-20261005` | 2 |
| `pr8842-evidence-r01` | 1 |
| `repo-cleanup-r71-20261019` | 1 |
| `repository-consolidation-20261019` | 6 |
| `repository-consolidation-current-20261019` | 1 |
| `repository-inventory-r20-20261019` | 9 |
| `standard-caller-blocked-x11-a04-20261019` | 1 |
| `stdio-cancel-output-backpressure-20261020` | 2 |
| `x11-proxy-fake-relay-20261019` | 3 |

This census does not identify process/session owners, inspect ignored files,
prove branch/PR dependencies, or establish recoverability of untracked/raw
outputs. Normal clean status is not proof that a worktree is unused. No root
was moved, pruned, reset, archived, or deleted. Reconcile each dirty root and
its owner before any physical cleanup; retain unknown custody.
