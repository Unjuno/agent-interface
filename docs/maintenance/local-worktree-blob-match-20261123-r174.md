# Root worktree blob match audit r174 — 2026-11-23 UTC

Read-only follow-up to [custody snapshot r173](local-worktree-custody-recheck-20261123-r173.md), comparing the dirty root `main` working-tree blobs with current `origin/main` and every registered worktree's HEAD.

- Root checkout: `897f4896d23dd127a4523dc4955e573dace7d674`; current `origin/main`: `f9042aa32dd20024a33da0257c9acf645420cde6`.
- `git rev-list --left-right --count main...origin/main` returned `0 170`: root main is 170 commits behind and has no unique commits ahead.
- Root status contains 21 entries: 11 tracked modifications and 10 untracked paths.
- Three modified tracked files are byte-identical to current-main blobs and to committed copies in registered worktrees:
  - `research/integration/standard_mcp_task_ledger_57_v1/test_mcp_endpoint_composition.py` — `44fd453cda316a47b44bf2af48c2b5ebd0bc38c8`
  - `runtime/guarded_x11_v1/calc_task_artifact_v1.py` — `14d652de43941c929d64d23fffeb18882f0827cb`
  - `runtime/guarded_x11_v1/test_calc_task_artifact_v1.py` — `20259e9d268a4d0f9937f0d8f4f44ce55e41b316`
- The other eight tracked modified files did not match any registered worktree HEAD blob in the byte-level scan. Their ownership and meaning remain unresolved; the ten untracked paths also remain untouched.

These three status markers are stale-checkout differences, not unique worktree edits. This does not make the root worktree clean: its current branch is far behind main and the remaining dirty/untracked data still needs custody reconciliation. No file was restored, staged, deleted, or overwritten.

Reproducible check: for each file, `git hash-object --path=<path> -- <path>` was compared to `git rev-parse origin/main:<path>` and to each registered worktree's `HEAD:<path>`. All three listed hashes matched exactly.
