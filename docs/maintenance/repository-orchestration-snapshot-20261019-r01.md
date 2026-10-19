# Repository orchestration and worktree snapshot r01

Captured 2026-10-19 from the live GitHub repository and registered local Git worktrees. This is a discovery/custody map, not semantic triage or an authorization to merge, close, delete, or reuse any checkout.

## Current baseline

- Remote `main`: `9d7345e5fc66d5b64f149d6ca45114d78fac7ce0` (PR #9177 evidence merge).
- Live open membership: 1,673 Issues and 482 PRs (GitHub GraphQL count). All 482 open PRs were fetched with exact head/base refs and SHAs; this report matches local worktree branches to open PR head branch names.
- Existing family/issue disposition strategy: [REPOSITORY_CONSOLIDATION.md](../REPOSITORY_CONSOLIDATION.md). Idea routing coverage is not semantic triage; open-item membership is not ownership.
- The current computer-control goal remains active. This cleanup record does not replace it or declare it solved.

## Registered worktrees

`dirty` lists tracked/untracked paths reported by `git status --porcelain --untracked-files=all`; ignored files and running processes were not inspected. Owner is unknown unless established by a separate current handoff. A PR branch-name match is a navigation hint, not proof of owner or that its checkout contains the current PR head.

| Checkout label | Branch / state | HEAD | Worktree | Changed paths (up to 8) | Open PR head match |
|---|---|---|---|---|---|
| agent-interface | `integration/x11-fake-socket-relay-r01` | `994f18dcd479` | dirty (3 paths) | docs/CURRENT_GOAL.md, docs/INTEGRATION_PLAN.md, docs/WORKER_WORK_MAP.md | — |
| pr7370-independent-review | `(detached)` | `aebf4ac28a84` | clean | — | — |
| pr7660-independent-test | `(detached)` | `279577b515b2` | clean | — | — |
| pr7660-independent-test-current | `(detached)` | `6d3b1017fc29` | clean | — | — |
| mindustry-current-main-audit-20261005 | `research/57-compiled-efficiency-v2-20261005` | `31095132d080` | dirty (92 paths) | "research/live_control/interface-edge-frame-ocr-6yn05yzl/profile/ [generated browser-profile state; detailed paths redacted]| — |
| pr9171-current-main-recheck-r01 | `research/9171-current-main-recheck-r01` | `3b94963440a2` | clean | — | — |
| release-expiry-queued-press-mcp-20261018 | `runtime/fake-x-release-order-followup-20261019` | `38300c7275ad` | clean | — | — |
| repo-cleanup-r71-20261019 | `research/xres-wire-fake-relay-r01` | `627223a97247` | dirty (1 paths) | runtime/cli_v1/test_mcp_relay_composition.py | — |
| repo-orchestration-cleanup-status-r01 | `docs/orchestration-cleanup-status-r01-20261019` | `9d7345e5fc66` | clean | — | — |
| repository-consolidation-20261019 | `test/xorg-xres-disconnect-fence` | `4ffa711d6bf4` | dirty (6 paths) | docs/REPOSITORY_CONSOLIDATION.md, docs/WORKER_WORK_MAP.md, docs/ideas/README.md, docs/maintenance/open-issues-20261019-r20.csv, docs/maintenance/open-prs-20261019-r20.csv, docs/maintenance/repository-inventory-20261019-r20.md | — |
| repository-inventory-r20-20261019 | `docs/repository-inventory-r20-20261019` | `5ae50f1a8f77` | dirty (9 paths) | docs/IDEAS_AND_OUTCOMES.md, docs/REPOSITORY_CONSOLIDATION.md, docs/ideas/safety-control-agenda.md, docs/superpowers/plans/2026-10-19-repository-convergence.md, docs/maintenance/open-issues-20261019-r71.csv, docs/maintenance/open-prs-20261019-r71.csv, docs/maintenance/repository-inventory-20261019-r71.md, docs/maintenance/repository-surface-map-20261019.md | — |
| repository-inventory-r21-20261019 | `docs/repository-inventory-r21-20261019` | `e8ffb8cca024` | clean | — | — |
| repository-inventory-r83-20261019 | `research/x11-server-disconnect-order-r01-20261019` | `ec72ff539582` | clean | — | — |
| standard-caller-blocked-x11-a04-20261019 | `research/standard-caller-blocked-x11-a04-20261019` | `95386ee7e10e` | dirty (5 paths) | research/integration/standard_caller_blocked_x11_release_a04_20261019/conditions.json, research/integration/standard_caller_blocked_x11_release_a04_20261019/live_proxy.py, research/integration/standard_caller_blocked_x11_release_a04_20261019/probe.py, research/integration/standard_caller_blocked_x11_release_a04_20261019/requirements.lock, research/integration/standard_caller_blocked_x11_release_a04_20261019/run_once.py | — |
| temporal-sheet-idea-family-r01 | `docs/temporal-sheet-idea-family-r01` | `85c6e1edd9c5` | clean | — | — |
| verify-pr-8794 | `integration/1998-a06-main` | `86d08849e7c7` | clean | — | — |
| x11-proxy-fake-relay-20261019 | `research/x11-proxy-fake-relay-20261019` | `f9e3f1d72e06` | dirty (3 paths) | research/integration/offline_proxy_reply_framing_20261019/proxy_candidate.py, research/integration/offline_proxy_reply_framing_20261019/relay_candidate.py, research/integration/offline_proxy_reply_framing_20261019/test_relay_candidate.py | — |
| xres-18s-observation-run-20261019 | `docs/xres-18s-observation-run-20261019` | `16e69150d1ae` | clean | — | — |
| xres-idle-client-control-20261019 | `test/owned-xres-pid-cancel-composition-20261019` | `2affa665218a` | clean | — | — |
| xres-post-horizon-bound-20261019 | `test/xorg-xres-post-horizon-bound-20261019` | `d3dd3152206d` | clean | — | — |
| xvfb-blocked-caller-release-r01 | `research/xvfb-blocked-caller-release-r01` | `7a000fc62c8a` | clean | — | [#9171](https://github.com/Unjuno/agent-interface/pull/9171) @ 3b94963440a2 |
| xvfb-timing-compare-r01-20261019 | `research/xvfb-timing-compare-r01-20261019` | `a02226d9f221` | clean | — | — |
| codex-v39-pending-main-a01-20261008 | `research/59-v39-pending-invalidation-currentmain-20261008` | `cae208b3ab11` | clean | — | — |

## Immediate reconciliation points

- Open PR [#9171](https://github.com/Unjuno/agent-interface/pull/9171) currently points at `3b94963440a2fc1bef4b3da89d40626e3c4044f3`. The checkout `xvfb-blocked-caller-release-r01` has the same branch name but local HEAD `7a000fc62c8a`; it is stale relative to the live PR. A separate clean checkout `pr9171-current-main-recheck-r01` is at the exact live head. Keep both until their user/task owner and ignored files are resolved; use the exact-head checkout for any review of the current diff.
- The dirty `repository-consolidation-20261019` and `repository-inventory-r20-20261019` checkouts both modify `docs/REPOSITORY_CONSOLIDATION.md`; other shared-index edits also exist. They are a known write collision and must not be given to independent workers simultaneously.
- This table records only visible Git changes; it intentionally omits generated browser-profile file names. It does not establish whether ignored data or a process is still active.
## Findings and safe next actions

- Multiple checkouts contain uncommitted shared-document edits, including the root checkout and the existing consolidation/inventory checkouts. Keep them untouched until their exact author, output custody, and relationship to a current PR or task are established. Do not cherry-pick them by branch name alone.
- Clean status does not prove a checkout is disposable: detached PR review trees and experiment trees can still contain required context outside Git, ignored files, or running processes. No worktree or branch was removed in this snapshot.
- The matching PR head SHA is shown for direct comparison. A matching branch name with a different local HEAD needs a fresh exact-diff review; no automatic update or cleanup follows from this table.
- A practical worker may start only from a distinct family/PR packet with its exact source SHA, allowed paths, unique output directory, dependency/owner boundary, and finite stopping condition. Shared indexes and worker maps still need one integrator at a time.
- Next cleanup batch: reconcile the dirty consolidation/inventory worktrees against open PRs and any active user task; record a named custodian or hold reason for each. Then choose one small family with source/evidence already available and write its individual Issue dispositions before changing remote state.

This snapshot changes no Issue or PR state and makes no claim that all 1,673 Issues or 482 PRs have been semantically triaged.


## Post-capture reconciliation — PR #8799

At 2026-10-19 10:23:23 UTC, PR [#8799](https://github.com/Unjuno/agent-interface/pull/8799) merged as `b163da3cbc252b6bf07942d32e7e78185ad53761`. Its exact head was `47fa267195f9777bc5238f424196aa4852034763`; local integration validation applied that change cleanly to the then-current main `9d7345e5fc66d5b64f149d6ca45114d78fac7ce0`. On the integrated tree, the relevant stdio/exchange/UTF-8/failure-order tests passed 49/49 with a fresh `PRIMARY_FAILURE_EVIDENCE` directory, and the terminal-first-failure suite passed 6/6 with the workflow's `--experimental-vm-modules` flag. `git diff --cached --check` passed. The first local attempt lacked those fixture/VM options and failed before completing; it was rerun with the workflow conditions above. The existing PR checks were green except the unrelated formal check, which was skipped. The full integration-check workflow was not rerun locally.

Immediately after the merge, GitHub reported 1,673 open Issues and 481 open PRs (one fewer open PR; Issue membership unchanged). The 482/1,673 counts in the baseline table above remain the pre-merge snapshot. No Issue was closed, and no worktree or branch was removed in this reconciliation.

The temporary `outputs/pr8799-current-main-review` worktree created for this validation was removed after recording the result; its generated test witnesses were not part of the repository. The pre-existing worktrees in the inventory were left untouched.

At 2026-10-19 10:26:25 UTC, PR [#8781](https://github.com/Unjuno/agent-interface/pull/8781) merged as `29e8005d7223d6b4b765a67d46e093e6c27ea112`. Its head `d8f6bb83aee86fca92d432bfa9d173db1ec3ecc2` applied cleanly to main `b163da3cbc252b6bf07942d32e7e78185ad53761`; the new startup-input-failure test passed 1/1 locally, and `git diff --cached --check` passed. Existing build, native-mcp, and replay-gate checks were green; formal was skipped. Its temporary review checkout was removed after the test, with no ignored files present.

The live open set is now 1,673 Issues and 480 PRs; both merged PRs reduce the open PR count by one each. This updated membership was read from GitHub immediately after the second merge.

## PR #8789 disposition after current-main preview

PR [#8789](https://github.com/Unjuno/agent-interface/pull/8789) remains an open draft at head `27ddd98c185a832d607cf610853de8376bec0d81`. Its merge preview onto current main `29e8005d7223d6b4b765a67d46e093e6c27ea112` was conflict-free, but its focused test failed on this Windows host (Python 3.11.9): the concurrent stderr-drain arm did not observe `READY` within the test's fixed 2-second deadline. The dedicated Ubuntu 24.04 workflow passed on the PR head earlier; that does not validate the current-main merge preview on Ubuntu. Keep the PR draft/open and its claim limited to the Ubuntu fixture. The finite release condition is a current-main run on Ubuntu 24.04, or an explicit owner decision that the platform-specific result is sufficient. This local Windows failure is not evidence about the production V39 launcher or live GUI control. The temporary review worktree was removed after recording this boundary.

The latest live membership remains 1,673 open Issues and 480 open PRs. No Issue or PR status was changed for #8789.
