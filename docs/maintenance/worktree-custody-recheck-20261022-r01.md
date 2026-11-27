# Linked worktree custody recheck r01 — 2026-10-22

This is a read-only local custody audit after main 08064035460187ba5c8c5cbb2f4e9732ca622ada (PR #9399). It inspected the linked worktree registry, per-worktree status, commit ancestry against origin/main, patch equivalence with git cherry, and GitHub PR records. It did not read or execute experiment raw reports except the representative README files named below. No file inside either audited worktree was copied, edited, reset, cleaned, archived or deleted.

## Registry-wide result

The linked Git worktree registry contained 48 paths. All 48 were reachable to git status; 34 were clean and 14 had changes (5 detached). No registered branch name exactly matched an open PR head. This is a routing/custody discrepancy, not proof that a branch is abandoned: worktree ownership, remote relationship, task assignment and unique evidence still require reconciliation.

## High-volume worktree A

- Local path label: work/repository-cleanup-plan-r01-20261020
- Branch/head: research/owned-cancel-supervisor-prototype-r01 at 24e5fbd0823f0a8adbbad85830da2e639b8ecc91
- Against origin/main: 7 commits ahead, 141 behind; all seven are patch-unique under git cherry. No matching remote branch or PR was found.
- Committed branch diff: 112 paths, 19,372 insertions, 10 deletions.
- Working-tree status: 42 tracked modifications and 18,365 untracked entries. The untracked count includes 17,830 under research/integration/ and 507 under lib/python3.12/site-packages/; it also includes bin/ and pyvenv.cfg.
- Completeness caveat: status emitted “could not open directory 'lib64/': Function not implemented”. The count is what Git reported, not a complete filesystem inventory.
- Representative evidence read: research/integration/public_compiled_v2_six_task_fakex_20261021/README.md reports deterministic six-task Fake X composition, with runtime task success null and no external model calls, WSLc, Docker, live application, MAP01, matched arms or reliability population. The adjacent App Server adapter Fake X README likewise identifies the App Server as a test double and excludes provider timing/billing and matched efficiency. These descriptions do not classify every untracked file in this worktree.

Disposition: preserve. This local branch has unique commits and the worktree has extensive uncommitted/untracked state, but no current owner, remote PR or verified transfer destination has been established. It is not safe to merge wholesale or discard.

## High-volume worktree B

- Local path label: worktrees/primary-mint-sparse
- Branch/head: feat/prestarted-cancel-supervisor-r01 at 76626da8b03df25024d12efb5f1dde2f12c53ed2; the remote branch still exists.
- PR relationship: PR #9315 is CLOSED and unmerged. Its final comment marks the historical branch superseded and says committed packet paths/manifests were transferred via #9333, merged at 4fe158d2f5e3774580c3812c3c589fbc64d4f8d2. A closed historical PR is not an owner record for the current worktree changes.
- Against origin/main: 21 commits ahead, 136 behind; all 21 are patch-unique under git cherry. The committed branch diff touches 183 paths (33,273 insertions, 63 deletions).
- Working-tree status: 15 tracked modifications and 5,135 untracked entries: 4,809 under research/integration/standard_mcp_task_ledger_57_v1/, 315 under research/integration/public_mcp_prestarted_cancel_supervisor_20261021/, and 11 across the two untracked WSLc snapshot folders.
- WSLc boundary: the untracked r01/r02 snapshot READMEs say the empty global listing and transient creator PID do not prove an unused lane; they leave #7924 on HOLD and say not to launch an experiment. The current live Issue #7924 is OPEN/STOP. No WSLc command was run in this audit.

Disposition: preserve. The supersession receipt supports the committed historic transfer only; it does not establish custody of the 15 tracked modifications or the 5,135 untracked entries. Do not reuse the closed PR branch as a merge candidate, and do not clean or archive this worktree.

## Next safe action

Identify the current task/worker owner for each path. Then compare the untracked packet manifests and source identities with current main without running experiment runners. If unique useful material remains, prepare a small current-main transfer PR and verify its hashes and exact scope before considering branch/worktree retirement. Until ownership and transfer are verified, retain both worktrees and their contents.
