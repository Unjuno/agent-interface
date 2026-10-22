# Targeted worktree custody follow-up r02 (2026-10-22)

Captured 2026-10-22 03:18:33 UTC. Current `origin/main` was `1a21bef00c431af02fa7f280c7589b48d03402af`. This supplements, and does not overwrite, the [r01 read-only census](worktree-custody-census-20261022-r01.md). No dirty worktree was edited, tested, reset, archived, or deleted.

## `work/repository-cleanup-plan-r01-20261020`

- Worktree HEAD `24e5fbd0823f0a8adbbad85830da2e639b8ecc91`, branch `research/owned-cancel-supervisor-prototype-r01`.
- Relative to current main, the branch has 7 worktree-only commits and is 89 commits behind. GitHub returned `No commit found for SHA` for the exact HEAD; no open PR head matches the branch.
- It has 18,407 porcelain status entries, including 18,365 untracked entries. Of the untracked paths, 17,851 are under `research/`, 507 under `lib/`, and the balance across runtime/bin/docs and environment metadata. The `lib/python3.12/site-packages` subtree alone contains 507 untracked entries.
- The untracked research roots include six-task Fake X/public-caller packets, real-app-server and Chromium caller packets, standard-caller blocked-I/O/recovery cohorts, and other cancellation experiments. This is a filename/path census only; contents, manifests, overlap, validity and custody were not inspected.

**Disposition:** local-only commits and substantial untracked evidence have no verified owner or recovery record. Retain intact. Do not publish, transplant, reset, or archive until source ownership and exact evidence transfer are established.

## `worktrees/primary-mint-sparse`

- Worktree HEAD `76626da8b03df25024d12efb5f1dde2f12c53ed2`, branch `feat/prestarted-cancel-supervisor-r01`, exactly the closed PR [#9315](https://github.com/Unjuno/agent-interface/pull/9315) head (closed 2026-10-21 20:57:31 UTC). Its closure records supersession by #9320/#9321 and a later exact-tree receipt; the historical branch remains.
- Relative to current main, its branch is 21 commits ahead and 84 behind. It has 5,151 status entries, including 5,135 untracked entries. Of those untracked paths, 4,809 are under `research/integration/standard_mcp_task_ledger_57_v1`, 315 under the public-MCP supervisor packet, and 11 under two WSLc owner-snapshot directories. The latter are only filenames, not an allocation or release receipt.
- The current worktree has modified `runtime/cli_v1/mcp_server.py` and `runtime/cli_v1/owned_guarded_session.py` that differ from current main. Its current `cancel_supervisor.py` and supervisor test bytes match current main; this does not make the whole worktree equivalent. The committed PR #9315 head was explicitly rejected for merging because its stale runtime removed supervisor-PID binding and unrelated-client resource-base reuse refusal. PR #9320/#9321 and the later reconciliation are the authoritative integrated line.

**Disposition:** PR #9315's tracked historical evidence was reconciled, but this census does not establish that the later uncommitted CLI edits or 5,135 untracked files are duplicates or disposable. Preserve intact; map the uncommitted delta to its owner and manifests before any recovery or archival action. The filenames under WSLc snapshots do not alter #7924's STOP/HOLD.

## Next action

Resolve the owner, task/session lineage, and recovery path of these two worktrees. Compare only their exact uncommitted paths and manifests against current main and source records after the owner is known. Then give each artifact one of: verified transfer, resumable assignment, or retained unresolved custody. Keep the remaining 12 dirty worktrees for a separate finite batch.

Commands used were read-only: Git worktree/status/revision queries, `git diff` path/stat comparisons, GitHub PR-head/status reads, and a commit-associated-PR lookup. No experiment allocation or container operation was used.