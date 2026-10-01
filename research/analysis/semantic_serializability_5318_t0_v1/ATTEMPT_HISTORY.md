# Attempt history — Issue #5318 T0

1. **Full checkout attempt:** Started from current remote main `3d6ffc76d535309cf3820ed33cb9327354f03648` in a new task-owned branch/worktree. Windows checkout exhausted C: while expanding the 101,138-entry tree at 31%; Git returned `No space left on device`. No experiment source had yet been executed. The failed checkout target was not found in Git's worktree registry and no partial directory remained.
2. **Sparse checkout recovery:** Removed only the empty local branch created for attempt 1 after verifying its tip equaled origin/main; created a new task-owned worktree at the same main SHA with sparse paths limited to the root docs, `docs/CURRENT_GOAL.md`, `ROADMAP.md`, and this additive evidence directory. No other worktree, branch, Docker image, or container was altered.
3. **Construction attempt 1:** Host stdlib suite had 5/6 tests pass. One test exposed a candidate conflict-classification ordering defect for trusted commutative integer additions. Formal was not invoked. The source was corrected before freeze and the fixed suite passed 6/6.

These are environment/construction events, not scientific formal outcomes. The formal allocation remains one-shot and is governed by `FREEZE.json`.

