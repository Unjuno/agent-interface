# Local worktree and work-directory custody overlay r01

**Captured:** 2026-10-19 12:19 UTC from the local Windows workspace after cleanup PR #9186 merged at `bee4b22ebc1166d2055b367aff5d363ee82848c7`.

This read is separate from GitHub Issue/PR membership and from the earlier 09:22 snapshot. It checks registered worktree path, exact HEAD, branch, path existence, and `git status --porcelain --untracked-files=normal`. It does not inspect ignored contents, running processes, human/task ownership, or files recursively inside unregistered folders. No existing worktree, output, ref, or file was modified or removed in this audit.

## Registered worktrees

There are **24 registered worktrees; all 24 paths exist**. Seven report tracked or untracked changes; the remaining 17 have a clean porcelain status at this capture. The rows below retain every exact HEAD observed in this scan; re-fetch each row before any cleanup.

| Worktree directory | Branch | HEAD | Changed entries | Custody |
|---|---|---|---:|---|
| `agent-interface` | `integration/x11-fake-socket-relay-r01` | `994f18dcd479` | 3 | HOLD; edits in current-goal, integration-plan, and worker map. |
| `mindustry-current-main-audit-20261005` | `research/57-compiled-efficiency-v2-20261005` | `31095132d080` | 2 | HOLD; untracked OCR evidence directories. |
| `repo-cleanup-r71-20261019` | `research/xres-wire-fake-relay-r01` | `627223a97247` | 1 | HOLD; uncommitted relay-composition test edit. |
| `repository-consolidation-20261019` | `test/xorg-xres-disconnect-fence` | `4ffa711d6bf4` | 6 | HOLD; edited documentation plus three untracked r20 inventory artifacts. |
| `repository-inventory-r20-20261019` | `docs/repository-inventory-r20-20261019` | `5ae50f1a8f77` | 9 | HOLD; staged/unstaged idea edits plus r71 inventories and crosswalk. |
| `standard-caller-blocked-x11-a04-20261019` | `research/standard-caller-blocked-x11-a04-20261019` | `95386ee7e10e` | 1 | HOLD; untracked A04 experiment packet. |
| `x11-proxy-fake-relay-20261019` | `research/x11-proxy-fake-relay-20261019` | `f9e3f1d72e06` | 3 | HOLD; uncommitted relay candidate and tests. |

| Clean worktree directory | Branch | HEAD |
|---|---|---|
| `outputs/pr7370-independent-review` | detached | `aebf4ac28a84` |
| `outputs/pr7660-independent-test` | detached | `279577b515b2` |
| `outputs/pr7660-independent-test-current` | detached | `6d3b1017fc29` |
| `pr9171-current-main-recheck-r01` | `research/9171-current-main-recheck-r01` | `54fbc0438d4e` |
| `release-expiry-queued-press-mcp-20261018` | `runtime/fake-x-release-order-followup-20261019` | `38300c7275ad` |
| `repo-orchestration-cleanup-status-r01` | `fix/x11-bounded-cancel-followup` | `d082081b4775` |
| `repository-inventory-r21-20261019` | `docs/repository-inventory-r21-20261019` | `e8ffb8cca024` |
| `repository-inventory-r83-20261019` | `research/x11-server-disconnect-order-r01-20261019` | `ec72ff539582` |
| `temporal-sheet-idea-family-r01` | `docs/temporal-sheet-idea-family-r01` | `85c6e1edd9c5` |
| `verify-pr-8794` | `integration/1998-a06-main` | `86d08849e7c7` |
| `xres-18s-observation-run-20261019` | `docs/xres-18s-observation-run-20261019` | `16e69150d1ae` |
| `xres-idle-client-control-20261019` | `test/owned-xres-pid-cancel-composition-20261019` | `2affa665218a` |
| `xres-post-horizon-bound-20261019` | `test/xorg-xres-post-horizon-bound-20261019` | `d3dd3152206d` |
| `xvfb-blocked-caller-release-r01` | `research/xvfb-blocked-caller-release-r01` | `7a000fc62c8a` |
| `xvfb-guarded-recovery-pr` | `test/xvfb-guarded-recovery` | `44b09d2a348f` |
| `xvfb-timing-compare-r01-20261019` | `research/xvfb-timing-compare-r01-20261019` | `a02226d9f221` |
| `D:/codex-v39-pending-main-a01-20261008` | `research/59-v39-pending-invalidation-currentmain-20261008` | `cae208b3ab11` |

The exact named edits above are custody signals, not an assertion that these are the only valuable files. Do not reset or archive these worktrees from this summary. Some zero-diff worktrees also contain ignored data or independent review state that this scan did not inspect.

## Unregistered immediate work directories

The workspace `work/` directory contains **188 immediate child directories that do not exactly match a registered Git worktree path**. A shallow metadata check found a top-level `.git` entry in two (`git-byte-check`, `git-byte-readback`) and none in the other 186. This does not establish that the 186 are disposable: they may contain evidence, generated deliverables, copied source, nested repositories, or worker state. The shallow check did not recurse, inspect file contents, or determine their owners.

Treat this as a distinct cleanup queue, not as a deletion list. The next bounded pass should inventory the 188 directory names and immediate metadata into a private, recoverable report, detect nested Git metadata without changing it, then join candidates to exact PR/Issue/family evidence and current worker/session ownership. Preserve every unresolved item. Start with the two `.git` directories because nested-repository custody is a separate high-risk case; do not move or delete them during discovery.

## Decision

The local repository surface is **not yet clean enough to certify for unrestricted orchestration**. The count of registered worktrees alone misses 188 adjacent directories; seven worktrees have changes, and ignored files/process ownership were not examined. This overlay provides an updated checkpoint, not a full cleanup completion claim. All removals require an item-specific evidence-preservation and owner check under the [repository cleanup plan](../REPOSITORY_CLEANUP_PLAN.md).
