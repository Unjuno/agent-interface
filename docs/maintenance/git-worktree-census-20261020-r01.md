# Git worktree custody census r01 — 2026-10-20

Captured at `2026-10-20T07:52:11Z`, before creating the temporary worktree for
this documentation update. Method: `git worktree list --porcelain`, then
`git -C <path> status --porcelain --untracked-files=normal` for each registered
root. This checks local status only; it does not establish owner, active process,
GitHub dependency, ignored-file, or evidence custody.

| Registered worktrees | Clean in this status view | Dirty | Locked | Prunable |
|---:|---:|---:|---:|---:|
| 32 | 22 | 10 | 0 | 0 |

## Dirty roots to preserve pending owner/evidence review

| Worktree | Branch | Status entries | Sample |
|---|---|---:|---|
| `agent-interface` | `integration/x11-fake-socket-relay-r01` | 23 | Modified documentation, additive maintenance receipts, and three untracked integration evidence packages. |
| `mindustry-current-main-audit-20261005` | `research/57-compiled-efficiency-v2-20261005` | 2 | Two untracked OCR output directories. |
| `pr8842-evidence-r01` | `rescue/pr8842-evidence-r01` | 1 | Untracked `work/` directory. |
| `repo-cleanup-r71-20261019` | `research/xres-wire-fake-relay-r01` | 1 | Modified relay-composition test. |
| `repository-consolidation-20261019` | `test/xorg-xres-disconnect-fence` | 6 | Modified consolidation/index files and untracked inventory data. |
| `repository-consolidation-current-20261019` | `integration/57-composition-plan-20261020` | 1 | Modified integration plan. |
| `repository-inventory-r20-20261019` | `docs/repository-inventory-r20-20261019` | 9 | Staged/unstaged idea index, consolidation, and safety family records. |
| `standard-caller-blocked-x11-a04-20261019` | `research/standard-caller-blocked-x11-a04-20261019` | 1 | Untracked A04 result package. |
| `stdio-cancel-output-backpressure-20261020` | `test/stdio-cancel-output-backpressure-20261020` | 2 | Modified relay implementation and regression test. |
| `x11-proxy-fake-relay-20261019` | `research/x11-proxy-fake-relay-20261019` | 3 | Modified proxy candidate and two untracked relay/test files. |

No dirty branch name exactly matched a head-branch name in the r108 open-PR
metadata (the r109/r110 rechecks confirm the same PR ID set). A literal
head-name mismatch does not show that a checkout is
unowned, inactive, unrelated as a PR base/dependency, or safe to remove. The
status command omitted ignored files; clean roots may still contain ignored
artifacts or active sessions. No branch or worktree was moved, pruned, reset,
archived, or deleted.

## Safe next step

For each root, identify its worker/session and task, compare its exact HEAD with
open and closed PR heads/bases and current main, then inspect ignored/untracked
data and evidence restore paths. Only an individually verified redundant root
with owner release and recoverable unique data can become a removal candidate.
