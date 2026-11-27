# Local worktree custody recheck r169 — 2026-11-23 JST

Read-only inventory of the registered worktrees for this checkout found 21
worktrees: 14 clean and 7 with tracked or untracked changes. The workspace-root
`outputs/` contains 12 files across two directories. This is a local custody
snapshot, not a repository-wide artifact inventory.

| Worktree | Branch/state | Changed status entries | PR status |
|---|---|---:|---|
| Main worktree | `main` | 21 | No PR; preserve as existing workspace changes |
| `issue57-calc-merged-main-20261121` | `codex/issue57-effect-clock-domain-r01` | 3 | #10367 merged; post-merge changes remain |
| `issue57-next-gate-main-20261121` | `codex/wslc-readonly-probe-20261121` | 1 | No PR found |
| `portable-runtime-current-main-acbdfc0f9-r01` | `docs/g10-currentmain-stdio-rerun` | 1 | #10392 merged; untracked output remains |
| `research-preview-host-recheck-20261122` | detached | 3 | Untracked evidence remains |
| `repository-inventory-r163-20261122` | `research/win32-current-main-fixture-repeat-r04-20261122` | 2 | Not matched to a PR in this pass |
| `_audit-pr10340-c47ae761` | detached | 2 | Raw log changes remain |

Two non-clean branches were confirmed to have merged PRs (#10367 and #10392),
but merged status alone does not resolve local
post-merge changes. No worktree or output was modified or deleted. Next steps
are owner/custody checks, byte-hash comparison against tracked evidence, and
only then deciding whether any exact duplicate can be removed.
