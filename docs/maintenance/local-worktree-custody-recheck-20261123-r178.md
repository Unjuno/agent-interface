# Local repository cleanup checkpoint r178

Captured 2026-11-23 against `origin/main` `fec81b7017a9e4d76d976dc78ee1ecabcf838346`.
The exact read-only inventory is in
[`local-worktree-custody-recheck-20261123-r178.json`](local-worktree-custody-recheck-20261123-r178.json).

## Current facts

- Complete paginated GitHub reads returned **1,640 open Issues and 403 open
  PRs**. Exact sorted ID sets match r177: zero additions and zero removals.
  This confirms inventory stability, not semantic disposition.
- The shared local Git registry contains **31 worktrees; 10 were dirty** at
  the JSON capture. Nine pre-existing dirty worktrees contain project work.
  The tenth is this checkpoint's authoring worktree, dirtied by the new receipt;
  it is expected to become clean when this documentation change is committed.
- The main checkout is itself dirty and contains tracked project documents,
  runtime/test edits, and many nested worktrees under `.worktrees/`. Recursive
  `--untracked-files=all` output expands nested trees into about 215,000
  entries; the retained snapshot uses normal mode and records 22 root status
  entries with untracked directories collapsed. Do not treat it as disposable
  residue.
- Other dirty trees contain an untracked WSLc diagnostic packet, a Calc
  post-merge result and manifest edits, Research Preview build/doctor outputs,
  launcher-test edits, Win32 composition-test output, and modified raw stderr
  in a detached audit. Preserve these until their content, source, owner, and
  Issue/PR linkage are checked.
- Branch lookup confirms some dirty trees descend from already merged PRs
  (#10367, #10392, #10489, #10435). A merged branch does not make its remaining
  uncommitted or untracked files redundant. The detached and no-result lookups
  remain unassigned; no owner is inferred from branch names.

## Cleanup decision

The repository is **not clean**. No cleanup mutation is justified by this
inventory alone. In particular, do not reset the dirty main checkout, delete
nested worktrees, remove ignored/untracked outputs, or close Issues from this
count-only comparison.

## Next bounded cleanup sequence

1. Reconcile the dirty root `main` checkout against `origin/main` by path and
   content hash. Mark each file as already integrated, unique evidence, active
   source change, or unresolved; preserve the last category.
2. For each of the other nine pre-existing dirty worktrees, map changed paths
   and hashes to its HEAD, branch, merged/open PR, Issue, and experiment packet.
   Keep detached outputs and failures intact until their custody is resolved.
3. Only after that mapping, transfer exact missing evidence or code into a
   reviewed branch, and archive a worktree only when its remaining bytes are
   verified duplicates or safely preserved elsewhere.
4. Refresh complete Issue/PR membership only when a disposition batch or
   substantive queue change warrants it; triage ideas family by family against
   the existing r160 crosswalk. Retain viable research and close/supersede only
   with an evidence-backed successor or outcome.

This is a read-only custody census and cleanup handoff. No worktree, branch,
file, Issue, or PR was deleted, reset, moved, closed, or merged for this
checkpoint.
