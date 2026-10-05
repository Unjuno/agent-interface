# Repository cleanup inventory — 2026-10-05

This is a dated, read-only inventory to support safe consolidation. It is not an authorization to merge, close, or delete anything. Refresh GitHub state before acting.

## Snapshot

- Repository: [Unjuno/agent-interface](https://github.com/Unjuno/agent-interface)
- API default branch tip observed: `11445a7ca200404ddc80bf7ebb1dbef86eb059de` (2026-10-05 16:24 JST).
- A `git fetch origin main` and `git ls-remote origin refs/heads/main` check confirmed the same tip after an earlier stale `origin/main` at `7a9398add78d9095e5a85a60d324513fc3c2a1e3`.
- Open PRs: **338** (52 ready, 286 draft); 282 target `main`, 56 target another branch.
- Open PR check rollup: **294 success, 12 failure, 1 pending, 31 without a check state**. All 338 had an unset GitHub review decision at capture; that field alone does not prove no comments exist.
- Remote branches: **391**; no branch-protection rule or repository ruleset was reported. Repository metadata has `delete_branch_on_merge=false`.
- Local worktrees observed: four, including three separate Issue #59 worktrees. Do not prune these based on remote branch counts.

## Verified integration during this inventory

- PR [#8067](https://github.com/Unjuno/agent-interface/pull/8067), “test(#59): block later input after persistent release loss,” merged at `2026-10-05T07:23:57Z` as merge commit `64dcc4c677202eb9b1c9b41ff808e56486c8321f`. The PR changed one test file; `audit`, `native-mcp`, `replay-gate`, and `research-workspace-index` all passed. The branch was retained because auto-delete is disabled.
- This is a verified example of a small mergeable change, not a blanket precedent: inspect each PR's own body, review requirements, base/head, latest checks, and dependencies.

## Recent Issue #59 cluster

| PR | Title | State at capture | Base | Disposition |
|---|---|---|---|---|
| #8071 | preserve A07 candidate launch STOP | ready | main | No disposition assigned; refresh review/checks and inspect dependencies |
| #8067 | block later input after persistent release loss | merged | main | Merged as `64dcc4c`; preserve branch for review/audit history |
| #8066 | preserve V39 release-order one-shot evidence | draft | main | No disposition assigned; refresh review/checks and inspect dependencies |
| #8065 | compose V39 renewal and per-key feedback paths | draft | main | No disposition assigned; refresh review/checks and inspect dependencies |
| #8064 | preserve corrected V39 retained diagnosis on current main | draft | main | No disposition assigned; refresh review/checks and inspect dependencies |
| #8062 | validate effect-indexed semantic deoptimization | draft | main | No disposition assigned; refresh review/checks and inspect dependencies |
| #8059 | exercise V39 pending-model invalidation ordering | draft | main | No disposition assigned; refresh review/checks and inspect dependencies |
| #8050 | preserve invalidation replay evidence | draft | main | No disposition assigned; refresh review/checks and inspect dependencies |
| #8031 | preserve health invalidation through pending planner handoff | draft | main | No disposition assigned; refresh review/checks and inspect dependencies |

The aggregate count and CSVs are the paginated snapshot; individual PR rows were refreshed after that capture where live state had changed (for example, #8067 merged during this inventory). Do not treat this short cluster table as a second complete export.

Observed relationships that need attention before consolidation:

- #8050 contains retained snapshots and test evidence associated with #8031/#8059. The evidence sets are overlapping; merging both without a path-level review may duplicate records.
- #8031 is an implementation proposal and #8050 is evidence-only. Both were draft with no review decision at capture. Keep them separate until review establishes whether implementation and evidence should land together.
- #8059 is a construction evidence PR sharing `research/doom/v39_pending_model_invalidation_a01_20261005/` with #8050. Treat the latter as a potential duplicate publication; compare exact trees and issue chronology before closing either.
- Non-main-base PRs require stack-order review. 56 open PRs targeted 38 distinct non-main branches, so these are not independent mainline candidates.

## Safe consolidation rules

1. Preserve every OPEN PR head branch and every branch referenced as another open PR base/head.
2. Never merge a draft. For ready PRs, verify required independent review quorum from that PR's body/Issue workflow, all required CI checks, current mergeability, and latest base SHA.
3. For stacked PRs, merge bottom-up only after each parent is accepted; do not retarget or close a child until its unique commits and evidence paths are mapped.
4. For closed-unmerged PR branches, retain until PR conversation, Issue references, dependent branches, and unique commits/evidence have been reviewed.
5. For merged branches, confirm merge commit and whether the tip or later commits are on current main. Do not delete automatically; branch auto-delete is disabled intentionally.
6. Keep failed/STOP evidence and failed CI attempts when they constrain later work. Add an index or disposition note instead of rewriting frozen evidence.
7. Make cleanup in small reviewable PRs, each with before/after counts, exact branch SHA, unique commit/path audit, owner/dependency status, and independent review.

## Retrieval notes

- Open-PR counts came from paged GitHub GraphQL `repository.pullRequests(states: OPEN, first: 100)` and were cross-checked against REST pagination. A short `gh pr list` response was incomplete and was not used for totals.
- The branch name/tip snapshot came from REST `repos/Unjuno/agent-interface/branches` pagination (391 records). An all-branch ancestry audit did not complete in this session; **no branch is classified safe to delete**.
- Review decisions are unset for the captured open PRs, and branch protection/rulesets were absent. This means repository settings do not enforce the review gates; maintainers must respect per-PR instructions.
- The older [2026-10-01 inventory](BRANCH_INVENTORY_20261001.md) remains an immutable prior snapshot; this file supersedes its counts, not its provenance.

## Next pass

1. Export complete PR state, all reviews/comments, and commit/file lists at a single captured time.
2. Map all 391 branch tips to open, closed, and merged PRs; then compute unique commits against the relevant base and identify dependent open refs.
3. Group exact duplicate evidence publication and superseded candidates; request owner disposition for unresolved and private-resource branches.
4. Merge only individually reviewed ready PRs whose required checks pass against the current base. Record merge commit, retain the branch initially, and prune only after unique commits and evidence are verified present elsewhere.
