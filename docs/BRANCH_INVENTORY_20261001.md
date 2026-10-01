# Branch inventory snapshot — 2026-10-01

This is a point-in-time inventory, not a deletion list. Branch tip and PR state can change immediately; refresh them before acting.

## Snapshot

- Repository: [`Unjuno/agent-interface`](https://github.com/Unjuno/agent-interface)
- Default branch: `main`
- Main at initial GitHub MCP inventory: `45395880f873f1592bc188a37471d8380535e1ec`.
- Main advanced during this audit to `bd9c4c5ceca68f4dc09bb39d27b140a987b68656` (`research(#5791): audit anti-windup source eligibility (#5844)`). The maintenance branch was rebased onto this tip before PR creation.
- GitHub REST returned 320 branch refs on pages 1–4 (100 + 100 + 100 + 20). Branch names, commit SHAs, and page responses were retained in the task transcript; they were not captured as a complete local CSV in this change.
- Open PR listing returned 5 entries at the observed instant: #5843 (ready/open), #5831 (draft), #5823 (draft), #5818 (draft), and #5815 (draft). Refresh the canonical [open PR list](https://github.com/Unjuno/agent-interface/pulls?q=is%3Apr+is%3Aopen) before each action.
- Open Issues are numerous (repo metadata reported 1,243); no full issue export or mass issue state change was performed.

## Disposition rules

1. **Open PR or draft:** preserve the head branch, even when the formal run is blocked. A draft can contain the only tested scaffold or preserve a consumed STOP. Check the PR body and latest comments before treating it as stale.
2. **Merged PR:** verify `merged_at`, merge commit, and whether the branch tip is included in current `main`. A merged PR alone does not prove the entire branch is disposable: check later commits and other dependent PRs.
3. **Closed, unmerged PR:** inspect the close reason and branch-only commits. Retain evidence not present on main; only then consider archiving or deleting.
4. **No PR:** check whether commits are ancestors of main, associated with open/closed Issues, referenced as a base/head by another branch, and whether their files are the only copy of raw results. Unknown means retain.
5. **Concurrent work:** do not delete a branch while an owner has a frozen run, resource allocation, active session, or publication handoff. Keep research branches additive and use unique result paths.

## What this audit established

The high branch count is real, and many names are research allocations with dates, Issue IDs, versions, or preservation/rescue intent. The inventory interfaces expose branch tips and PR summaries but do not expose a reliable, machine-verifiable “safe to delete” signal. Therefore this snapshot does **not** classify individual branches as stale and authorizes no branch deletions. Existing repository guidance in `docs/ISSUE_FAILURE_CLASSIFICATION.md` and [Worker Quickstart](../../docs/WORKER_QUICKSTART.md) remains the operational cleanup gate.

## Next safe cleanup pass

Generate a fresh table from GitHub REST `branches`, open and closed PRs, Issue references, and Git ancestry. Suggested columns: branch, tip SHA, merged into main, PR state/number, Issue IDs, unique commits, unique evidence paths, latest update, owner/allocation, disposition, and reviewer. Propose deletion only for rows whose evidence and dependency fields are all resolved; retain the input snapshot and reviewed table in the cleanup PR.
