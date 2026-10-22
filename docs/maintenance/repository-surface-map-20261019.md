# Local repository surface and custody snapshot — 2026-10-19

Captured 2026-10-19 09:22 UTC on the attached Windows workspace, from `git worktree list --porcelain` and per-worktree `git status --porcelain=v1 --untracked-files=all`, `git ls-files --others -i --exclude-standard`, and HEAD/upstream queries. Repository common dir: `work/agent-interface/.git`.

This is a local workspace snapshot, not a GitHub Issue/PR inventory and not a complete process/owner audit. It is additive; no worktree, ref, ignored file, or output was modified or removed. `Changed` counts include tracked modifications and untracked files; `Ignored` counts are Git-ignored files and are not safe-to-delete classifications.

| Worktree | Branch / HEAD | Changed | Ignored | Disposition |
|---|---|---:|---:|---|
| `work/agent-interface` | `integration/x11-fake-socket-relay-r01` / `994f18dcd479` | 46 | 232 | HOLD: broad uncommitted documentation/runtime work; preserve. |
| `outputs/pr7370-independent-review` | detached / `aebf4ac28a84` | 0 | 1 | HOLD: independent review checkout; linked PR/session not established. |
| `outputs/pr7660-independent-test` | detached / `279577b515b2` | 0 | 7 | HOLD: independent test checkout; linked PR/session not established. |
| `outputs/pr7660-independent-test-current` | detached / `6d3b1017fc29` | 0 | 0 | HOLD: independent test checkout; linked PR/session not established. |
| `work/mindustry-current-main-audit-20261005` | `research/57-compiled-efficiency-v2-20261005` / `31095132d080` | 92 | 31 | HOLD: 92 untracked browser-profile/session files plus ignored bytecode; owner and raw-data custody unresolved. |
| `work/release-expiry-queued-press-mcp-20261018` | `runtime/fake-x-release-order-followup-20261019` / `38300c7275ad` | 0 | 460 | HOLD: ignored files include `research/integration/xres_blocked_owner_release_a02_20261019/raw/wslc-run-raw.log` through A09 equivalents; preserve and verify ownership/manifest before any cleanup. |
| `work/repo-cleanup-r71-20261019` | `research/xres-wire-fake-relay-r01` / `627223a97247` | 1 | 110 | HOLD: active uncommitted test edit. Directory name is misleading; branch is XRes/Fake-X research. |
| `work/repository-consolidation-20261019` | `test/xorg-xres-disconnect-fence` / `4ffa711d6bf4` | 6 | 231 | HOLD: uncommitted inventory CSVs and docs; retain as current author work. |
| `work/repository-inventory-r20-20261019` | `docs/repository-inventory-r20-20261019` / `5ae50f1a8f77` | 0 | 0 | CLEAN checkout; contains convergence plan. |
| `work/repository-inventory-r21-20261019` | `docs/repository-inventory-r21-20261019` / `e8ffb8cca024` | 0 | 0 | CLEAN checkout; post-merge membership note. |
| `work/repository-inventory-r83-20261019` | `research/x11-server-disconnect-order-r01-20261019` / `ec72ff539582` | 0 | 86 | HOLD: clean tracked tree, but research branch and ignored runtime artifacts need PR/session lineage. |
| `work/standard-caller-blocked-x11-a04-20261019` | `research/standard-caller-blocked-x11-a04-20261019` / `95386ee7e10e` | 5 | 18 | HOLD: untracked experiment source/conditions; branch is 32 commits behind local `origin/main`. |
| `work/temporal-sheet-idea-family-r01` | `docs/temporal-sheet-idea-family-r01` / `85c6e1edd9c5` | 0 | 0 | HOLD: clean docs branch; issue/PR lineage not established. |
| `work/verify-pr-8794` | `integration/1998-a06-main` / `86d08849e7c7` | 0 | 15 | HOLD: verification checkout; owner/session and retained ignored files unresolved. |
| `work/x11-proxy-fake-relay-20261019` | `research/x11-proxy-fake-relay-20261019` / `f9e3f1d72e06` | 3 | 0 | HOLD: uncommitted relay candidate/tests; branch is 70 commits behind local `origin/main`. |
| `work/xres-18s-observation-run-20261019` | `docs/xres-18s-observation-run-20261019` / `16e69150d1ae` | 0 | 0 | HOLD: clean evidence branch; exact result packet/PR ownership not established by worktree scan. |
| `work/xres-idle-client-control-20261019` | `test/owned-xres-pid-cancel-composition-20261019` / `2affa665218a` | 0 | 145 | HOLD: tracked tree clean; ignored runtime outputs/bytecode need classification. |
| `work/xres-post-horizon-bound-20261019` | `test/xorg-xres-post-horizon-bound-20261019` / `d3dd3152206d` | 0 | 8 | HOLD: tracked tree clean; ignored test/runtime files need classification. |
| `work/xvfb-blocked-caller-release-r01` | `research/xvfb-blocked-caller-release-r01` / `7a000fc62c8a` | 0 | 82 | HOLD: PR #9171 experiment checkout; ignored files require preserving result/custody review. |
| `work/xvfb-timing-compare-r01-20261019` | `research/xvfb-timing-compare-r01-20261019` / `a02226d9f221` | 0 | 0 | HOLD: clean research checkout; current assignment/PR lineage not verified here. |
| `second-volume/codex-v39-pending-main-a01-20261008` | `research/59-v39-pending-invalidation-currentmain-20261008` / `cae208b3ab11` | 0 | 157 | HOLD: separate-volume research checkout; owner and ignored artifact custody unresolved. |

## Findings and next evidence

- 21 registered worktrees were observed. Six have tracked/untracked changes (the primary workspace, Mindustry audit, repo-cleanup-named XRes worktree, repository-consolidation worktree, standard-caller A04, and X11 proxy relay). The largest visible untracked set is 92 files in the Mindustry audit worktree; sample paths are Chromium profile storage files, so they may contain live session state and must not be deleted as build debris.
- The primary workspace has 46 changed files and 232 ignored files. It has no upstream configured. This inventory does not identify its author/session or compare its branch with current GitHub PR metadata.
- Two branches with an upstream are behind the locally cached `origin/main` by 32 and 70 commits. This is not a fresh remote comparison and does not establish that either branch is abandoned.
- `release-expiry-queued-press-mcp-20261018` contains hundreds of ignored files, including raw WSLc run logs. Their presence is evidence to preserve, not authorization to rerun or clean them.
- The `outputs` worktrees are verification/review artifacts, not ordinary feature branches. Their retention owner and intended expiry are unknown.
- `git worktree list` does not enumerate unregistered worktrees, non-worktree folders, GitHub PR ownership, running processes, or who currently owns a checkout. Those remain custody holds.

No cleanup action is approved by this snapshot. Before any branch/worktree/output disposition, reconcile each row with current GitHub PR head/base and assignments, identify the active session/process owner, inspect ignored/untracked manifests without modifying them, and record a recoverable copy or canonical evidence destination. The next independent pass should map each active worktree/ref to a live PR/Issue or a named research-family record; only then can a truly stale, ownerless item be proposed for archival.

## Worktree-to-open-PR head crosswalk

Joined each registered worktree's branch name and exact HEAD SHA against the 482 open PR rows in r85. Only one checkout matches both fields: `work/xvfb-blocked-caller-release-r01` is exact PR #9171 head `7a000fc62c8ad4704b277084a0d832959f82189a`. No other registered worktree has an exact open-PR head match. This is a lineage signal only: it does not show that the other 20 worktrees are abandoned, because their changes may be merged, closed, local-only, stacked, or tied to an Issue/session not represented by an open PR.

| Worktree | Branch | HEAD | r85 open-PR match |
|---|---|---|---|
| `work/agent-interface` | `integration/x11-fake-socket-relay-r01` | `994f18dcd479` | none |
| `outputs/pr7370-independent-review` | detached | `aebf4ac28a84` | none |
| `outputs/pr7660-independent-test` | detached | `279577b515b2` | none |
| `outputs/pr7660-independent-test-current` | detached | `6d3b1017fc29` | none |
| `work/mindustry-current-main-audit-20261005` | `research/57-compiled-efficiency-v2-20261005` | `31095132d080` | none |
| `work/release-expiry-queued-press-mcp-20261018` | `runtime/fake-x-release-order-followup-20261019` | `38300c7275ad` | none |
| `work/repo-cleanup-r71-20261019` | `research/xres-wire-fake-relay-r01` | `627223a97247` | none |
| `work/repository-consolidation-20261019` | `test/xorg-xres-disconnect-fence` | `4ffa711d6bf4` | none |
| `work/repository-inventory-r20-20261019` | `docs/repository-inventory-r20-20261019` | `5ae50f1a8f77` | none |
| `work/repository-inventory-r21-20261019` | `docs/repository-inventory-r21-20261019` | `e8ffb8cca024` | none |
| `work/repository-inventory-r83-20261019` | `research/x11-server-disconnect-order-r01-20261019` | `ec72ff539582` | none |
| `work/standard-caller-blocked-x11-a04-20261019` | `research/standard-caller-blocked-x11-a04-20261019` | `95386ee7e10e` | none |
| `work/temporal-sheet-idea-family-r01` | `docs/temporal-sheet-idea-family-r01` | `85c6e1edd9c5` | none |
| `work/verify-pr-8794` | `integration/1998-a06-main` | `86d08849e7c7` | none |
| `work/x11-proxy-fake-relay-20261019` | `research/x11-proxy-fake-relay-20261019` | `f9e3f1d72e06` | none |
| `work/xres-18s-observation-run-20261019` | `docs/xres-18s-observation-run-20261019` | `16e69150d1ae` | none |
| `work/xres-idle-client-control-20261019` | `test/owned-xres-pid-cancel-composition-20261019` | `2affa665218a` | none |
| `work/xres-post-horizon-bound-20261019` | `test/xorg-xres-post-horizon-bound-20261019` | `d3dd3152206d` | none |
| `work/xvfb-blocked-caller-release-r01` | `research/xvfb-blocked-caller-release-r01` | `7a000fc62c8a` | exact #9171 head |
| `work/xvfb-timing-compare-r01-20261019` | `research/xvfb-timing-compare-r01-20261019` | `a02226d9f221` | none |
| `second-volume/codex-v39-pending-main-a01-20261008` | `research/59-v39-pending-invalidation-currentmain-20261008` | `cae208b3ab11` | none |

Before any archival, map nonmatching refs by commit ancestry and closed/merged PR history, then compare active Issues/assignments and session ownership. Current open-PR branch-name/SHA comparison alone is not a cleanup criterion.

## Historical PR lineage crosswalk

A separate `gh pr list --state all --limit 5000` query returned exactly 5,000 unique rows, so it is capped and does not cover the entire closed-PR history. It did find positive head/branch matches for 15 merged PRs and one open PR across the 21 registered worktrees. The machine-readable matches and unresolved rows are in [worktree-to-PR crosswalk r01](worktree-pr-crosswalk-20261019-r01.csv). The 15 merged-PR associations are #9153, #7370, #7856, #9047, #9057, #9154, #9061, #9164, #9170, #8803, #9063, #9070, #9062, #9167, and #8643; #9171 is open. Of the merged associations, #9154 matches the repository-inventory-r20 branch and its merged head is an ancestor of the current plan commit; #8803 matches the exact HEAD SHA while the checkout uses a different local branch name. The other 13 merged associations match both branch and HEAD.

Five worktrees have no match in this capped historical query: the two PR #7660 test directories, the `repo-cleanup-r71` directory, the A04 standard-caller checkout, and the X11 proxy relay checkout. This is an incomplete history lookup, not evidence they are abandoned. Even a merged PR match only proves code lineage. Post-merge modifications, ignored raw data, worker/session ownership, and safe archival conditions remain separate unresolved questions.
