# Git worktree status census r05 — 2026-10-20

Captured at `2026-10-20T11:18:54Z`. Method: enumerate
`git worktree list --porcelain`, then run
`git -C <path> status --porcelain=v1 --untracked-files=normal` once for each
registered root.

| Registered roots | Existing | Clean in normal status | Dirty | Locked | Prunable |
|---:|---:|---:|---:|---:|---:|
| 37 | 37 | 27 | 10 | 0 | 0 |

## Dirty roots to preserve pending owner/evidence review

| Worktree | Status entries |
|---|---:|
| `agent-interface` | 31 |
| `mindustry-current-main-audit-20261005` | 2 |
| `pr8842-evidence-r01` | 1 |
| `repo-cleanup-r71-20261019` | 1 |
| `repository-consolidation-20261019` | 6 |
| `repository-consolidation-current-20261019` | 1 |
| `repository-inventory-r20-20261019` | 9 |
| `standard-caller-blocked-x11-a04-20261019` | 1 |
| `stdio-cancel-output-backpressure-20261020` | 2 |
| `x11-proxy-fake-relay-20261019` | 3 |

This records ordinary Git status only. It does not inspect ignored files,
process/session ownership, open/closed PR base dependencies, evidence
uniqueness, or recovery paths. No branch or worktree was moved, reset, archived,
pruned, or deleted. A clean status is not proof of staleness or permission to
remove a checkout. Resolve each dirty root individually and retain unknown
ownership.
