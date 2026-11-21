# Worktree and local-output custody recheck — 2026-11-22 JST

Read-only snapshot taken after PR #10427 merged. `origin/main` was
`d4e18c720328baa9d28d8179d75c39c3a39489f3`. The checkout table below comes
from `git worktree list --porcelain` and `git status --short`; “clean” means no
reported worktree changes, not that the branch is current or safe to delete.

| Worktree | HEAD | State | Disposition |
| --- | --- | --- | --- |
| `.goal-main-381a21-20261120` | `897f4896d2` | dirty (21 status entries), 70 commits behind origin/main | Preserve. Contains edits and untracked evidence/output folders; do not reset or remove wholesale. |
| `.goal-main-381a21-20261120/.worktrees/issue57-calc-fixture-r01` | `bdd1fb5772` | clean | Retain as an existing experiment checkout; no deletion decision made. |
| `.goal-main-381a21-20261120/.worktrees/issue57-calc-merged-main-20261121` | `f5f28c0f3b` | dirty (3) | Preserve. Its post-merge report lacks per-test Windows raw and its manifest paths are workspace-prefixed; newer PR #10425 evidence supersedes the discrepancy but not this historical custody record. |
| `.goal-main-381a21-20261120/.worktrees/issue57-cancel-timing-diagnostic-r01` | `b8130b847a` | clean | Retain pending semantic/custody routing. |
| `.goal-main-381a21-20261120/.worktrees/issue57-effect-clock-domain-postmerge-20261121` | `704d2a2b13` | clean | Retain pending semantic/custody routing. |
| `.goal-main-381a21-20261120/.worktrees/issue57-effect-receipt-handoff-main-20261121` | `ae10f768a8` | clean | Retain pending semantic/custody routing. |
| `.goal-main-381a21-20261120/.worktrees/issue57-native-owner-postmerge-r01` | `d18f24af4e` | clean | Retain pending semantic/custody routing. |
| `.goal-main-381a21-20261120/.worktrees/issue57-next-gate-main-20261121` | `e5866db03e` | dirty (1 untracked packet) | Preserve the WSLc read-only probe. It records only the EROFS read-only check; it is not live action/recovery or allocation evidence. |
| `.goal-main-381a21-20261120/.worktrees/portable-runtime-current-main-acbdfc0f9-r01` | `456b25eb80` | dirty (1 untracked packet) | Preserve the Research Preview fixture-mode result and hashes for a later gate/overlap audit. |
| `.goal-main-381a21-20261120/worktrees/issue57-calc-failure-integrity-20261122` | `aa24c2d31f` | clean | PR #10426 is merged; preserve checkout until branch/worktree cleanup is reviewed separately. |
| `.goal-main-381a21-20261120/worktrees/repository-inventory-r163-20261122` | `b61db8a509` | clean | PR #10427 merged as `d4e18c7203`; checkout is now one documentation commit behind main. |
| `_audit-pr10340-c47ae761` | `c47ae761ed` | dirty (2 modified raw stderr files) | Preserve byte-for-byte as audit evidence. |
| `worktrees/b13-dispositions-r160-20261121` | `c3bae65cfe` | clean | Retain pending branch/worktree reference audit. |
| `worktrees/integrate-7741-t0d-20261122` | `6c2b473fbc` | clean | Retain pending semantic/custody routing. |
| `worktrees/wslc-live-smoke-record-20261121` | `f8dbf9097c` | clean | Retain as stopped/record-only WSLc work; do not infer a live smoke from its name. |

Five worktrees are dirty and ten are clean. No dirty checkout was modified in
this audit. Clean worktrees are not automatically disposable: each still needs
a branch/PR reachability check and evidence-custody decision before removal.

Earlier content comparison found `research/integration/standard_mcp_task_ledger_57_v1/outputs/`
has 16 files, all byte-identical to current-main Git blobs (zero unique
contents); deletion of that exact directory was rejected by the environment
policy, so it remains untouched. Root `outputs/` has 122 files: 61 contents
match tracked current-main blobs and 61 are unique, including large game assets
and runtime/build outputs. Preserve the unique set. The older report and raw
packets under the dirty parent worktree also remain unclassified and must not
be treated as duplicate merely because another packet has the same topic.

Next custody pass: map each clean branch to its PR/merge base; review the five
dirty sets by file and hash; promote only independently useful evidence; then
remove a worktree only after its branch, unique files, and raw custody are
accounted for. This snapshot is a queue for that work, not a “clean repository”
claim.
