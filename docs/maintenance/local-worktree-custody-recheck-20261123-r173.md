# Local worktree custody recheck r173 — 2026-11-23 UTC

At `main` `bfddb91a39b4fefeff4a6de22c55fd661936dc62`, `git worktree list --porcelain` found 22 registered worktrees. Read-only `git status --porcelain --untracked-files=normal` returned 14 clean and 8 dirty worktrees. The exact per-worktree paths, revisions, branches, and status entries are retained in [r173 JSON](local-worktree-custody-recheck-20261123-r173.json).

The JSON SHA-256 is `19b0892fc984e7e50f84b52fa78eb95db6885e5edfc483bb479315010a2b1cf7`; see [checksum](local-worktree-custody-recheck-20261123-r173.json.sha256).

## Dirty custody requiring owner/reference reconciliation

| Worktree | Revision / branch | Status entries | Current reading |
|---|---|---:|---|
| `.goal-main-381a21-20261120` | `897f4896`, `main` | 21 | Numerous tracked source/doc edits plus untracked experiment/output directories. Preserve; working owner/custody is not established by this snapshot. |
| `.goal-main-381a21-20261120/.worktrees/issue57-calc-merged-main-20261121` | `f5f28c0f`, `codex/issue57-effect-clock-domain-r01` | 3 | Modified checksums/conditions plus untracked post-merge evidence. Reconcile against published PR and raw packet before cleanup. |
| `.goal-main-381a21-20261120/.worktrees/issue57-next-gate-main-20261121` | `e5866db0`, `codex/wslc-readonly-probe-20261121` | 1 | Untracked WSL read-only probe packet; preserve and map to its issue/PR. |
| `.goal-main-381a21-20261120/.worktrees/portable-runtime-current-main-acbdfc0f9-r01` | `456b25eb`, `docs/g10-currentmain-stdio-rerun` | 1 | Untracked bundle fixture packet; preserve and map to its published evidence. |
| `.goal-main-381a21-20261120/.worktrees/repo-current-main-audit-20261122` | `bfddb91a`, `maintenance/worktree-custody-r173-20261123` | 1 | Untracked nested `.worktrees/` registration/residue from the preview build investigation; contents and duplicate custody remain unresolved. |
| `.goal-main-381a21-20261120/.worktrees/research-preview-host-recheck-20261122` | `10b47b4b`, detached | 3 | Three untracked host/acceptance packets; preserve and link to current preview evidence. |
| `.goal-main-381a21-20261120/worktrees/repository-inventory-r163-20261122` | `b422191a`, `research/win32-current-main-fixture-repeat-r04-20261122` | 2 | Modified MCP test plus untracked output directory; identify whether it is the same experiment/output retained elsewhere before any consolidation. |
| `_audit-pr10340-c47ae761` | `c47ae761`, detached | 2 | Two modified raw stderr files; preserve exact bytes and identify the owning audit before resolution. |

The previous r169 snapshot found 21 worktrees (14 clean / 7 non-clean); r173 finds one additional registered worktree and eight dirty trees. This is a custody change, not proof that any dirty data is disposable. No file was deleted, reset, or overwritten. The active audit worktree's nested `.worktrees/` residue was left untouched.

## Next cleanup actions

1. Ask each experiment/branch record or merged PR to claim the corresponding dirty path; compare exact hashes and published packet contents.
2. Separate unique evidence, byte-identical duplicates, source modifications, and abandoned local-only output. Record duplicate proof before removal.
3. Keep the root `main` worktree intact until its 21 entries are reconciled and its unrelated active changes are committed or explicitly handed off.
4. Re-run the snapshot after custody resolution. Do not claim repository cleanliness until the registered tree and external workspace status are both reconciled.
