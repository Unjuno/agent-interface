# Local worktree and work-directory custody overlay r02

Captured 2026-10-19 14:38 UTC from the local Windows workspace. The scan ran `git worktree list --porcelain`, then checked each registered path's HEAD, branch, and ordinary porcelain status. It did not inspect ignored file contents, nested repositories below unregistered directories, or process/task ownership.

The scan found **26 registered worktrees; 8 had tracked or ordinary untracked changes**. The workspace `work/` contained **210 immediate child directories; 188 did not exactly match a registered Git worktree path**. Exact per-path state from the prior scan is in [custody overlay r01](worktree-custody-overlay-r01-20261019.md), but that snapshot is not current enough to authorize any disposition. Refresh the exact item before acting.

## Disposition

This is a custody HOLD, not a deletion queue. Counts, directory names, detached state, and a clean porcelain status do not establish that work is idle or disposable. Before disposition, inspect exact tip and commits, tracked/untracked/ignored evidence, PR/Issue/family linkage, owner/process/session, dependent work, and a recoverable copy. Use this overlay to avoid assuming the workspace is clean; it provides no permission to reset, archive, move, or delete any item.
