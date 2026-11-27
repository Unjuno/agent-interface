# Local repository cleanup checkpoint r179

Captured 2026-11-23T17:25:34Z against `origin/main` `164650754bce28fc849f630f0b744decb4034f87`. Exact local status data is in [the JSON snapshot](local-worktree-custody-recheck-20261124-r179.json).

## Current facts

- Complete pagination found **1,640 open Issues / 403 open PRs**, matching r177 membership: zero added or removed IDs. This is queue stability, not semantic disposition.
- The Git registry contains **33 worktrees; 10 dirty**. Status errors: 0. The root `main` checkout reports 22 porcelain entries in normal mode; `--untracked-files=normal` collapses directory contents, so this number is not a recursive file count.
- Every registered path, branch, HEAD, dirty count, status-code histogram, and status SHA-256 is retained in JSON. Nested worktrees are listed separately. Dirty bytes remain owned by their checkouts and have not been copied or changed by this read-only census.
- **The local repository is not clean.** This receipt does not attribute worktree ownership or prove duplicate contents. Do not reset, delete, move, or archive paths based on counts or merged branch ancestry alone.

## Next bounded cleanup sequence

1. Review dirty worktrees in priority order: root `main` and nested worktrees first, then active experiment/evidence trees; diff paths and hashes against their HEAD and current main.
2. Attribute each unique change to an owner, canonical Issue, PR, and experiment packet; distinguish exact duplicates from evidence with independent source bytes. Preserve unknown items.
3. Transfer or archive only after byte-level verification and retained provenance.
4. Continue family-by-family Issue/PR disposition; close/supersede only when outcomes and successors are linked. Do not optimize for lower counts.

No worktree, branch, file, Issue, or PR was deleted, reset, moved, closed, or merged for this census.
