# Branch inventory snapshot — 2026-10-01

This is a point-in-time inventory, not a deletion list. Branch tips, PR state, and counts can change immediately; refresh them before acting. The capture was incomplete for cleanup purposes: no full Issue export, per-branch ancestry/unique-commit table, or owner/dependency mapping was retained.

## Snapshot

- Repository: [`Unjuno/agent-interface`](https://github.com/Unjuno/agent-interface)
- Default branch: `main`
- Main at initial GitHub MCP inventory: `45395880f873f1592bc188a37471d8380535e1ec`.
- Main advanced during this audit to `bd9c4c5ceca68f4dc09bb39d27b140a987b68656` (`research(#5791): audit anti-windup source eligibility (#5844)`). The maintenance branch was rebased onto this tip before PR creation.
- GitHub REST returned 320 branch refs on pages 1–4 (100 + 100 + 100 + 20). Names and tips were inspected in the task session, but not captured as a complete local table; do not treat the transcript as an auditable inventory artifact.
- PR APIs disagreed during the session about current counts/states, and an initial open-PR search returned only five results while a later REST listing returned 67 open PRs. This establishes that the first list was incomplete. Refresh the canonical [open PR list](https://github.com/Unjuno/agent-interface/pulls?q=is%3Apr+is%3Aopen) and verify each target directly before acting.
- At capture, repository metadata reported `open_issues_count: 1243`; this is a historical metadata value, not an independently counted issue-only total. No full issue export or mass issue state change was performed.

## Disposition rules

1. **Open PR or draft:** preserve the head branch, even when the formal run is blocked. A draft can contain the only tested scaffold or preserve a consumed STOP. Check the PR body and latest comments before treating it as stale.
2. **Merged PR:** verify `merged_at`, merge commit, and whether the branch tip is included in current `main`. A merged PR alone does not prove the entire branch is disposable: check later commits and other dependent PRs.
3. **Closed, unmerged PR:** inspect the close reason and branch-only commits. Retain evidence not present on main; only then consider archiving or deleting.
4. **No PR:** check whether commits are ancestors of main, associated with open/closed Issues, referenced as a base/head by another branch, and whether their files are the only copy of raw results. Unknown means retain.
5. **Concurrent work:** do not delete a branch while an owner has a frozen run, resource allocation, active session, or publication handoff. Keep research branches additive and use unique result paths.

## What this audit established

The high branch count is real, and many names are research allocations with dates, Issue IDs, versions, or preservation/rescue intent. This audit did not compute ancestry or map all branches to PRs, Issues, paths, and owners. It therefore cannot say that any specific branch is stale. The snapshot classifies none as safe to delete and authorizes no branch deletions. Existing repository guidance in `docs/ISSUE_FAILURE_CLASSIFICATION.md` and [Worker Quickstart](WORKER_QUICKSTART.md) remains the operational cleanup gate.

## Next safe cleanup pass

Generate a fresh table from GitHub REST `branches`, open and closed PRs, Issue references, and Git ancestry. Suggested columns: branch, tip SHA, merged into main, PR state/number, Issue IDs, unique commits, unique evidence paths, latest update, owner/allocation, disposition, and reviewer. Propose deletion only for rows whose evidence and dependency fields are all resolved; retain the input snapshot and reviewed table in the cleanup PR.
