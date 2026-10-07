# Repository cleanup inventory — 2026-10-05

This is a dated, read-only inventory to support safe consolidation. It is not an authorization to merge, close, or delete anything. Refresh GitHub state before acting.

## Snapshot

- Repository: [Unjuno/agent-interface](https://github.com/Unjuno/agent-interface)
- API default branch tip observed: `11445a7ca200404ddc80bf7ebb1dbef86eb059de` (2026-10-05 16:24 JST).
- A `git fetch origin main` and `git ls-remote origin refs/heads/main` check confirmed the same tip after an earlier stale `origin/main` at `7a9398add78d9095e5a85a60d324513fc3c2a1e3`.
- During review, `main` advanced to `9146507c2689da7d4444d8febda848fa7dd4bcd1` and then `380c3d2b0e550a1b1defd6f1f5a0e3be80632028`; this inventory branch was rebased onto the latter tip. The CSVs remain the earlier fixed snapshot rather than a live view.
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

One inspected parent/child stack demonstrates the risk:

- #7440 targets `main`, is ready, and its recorded checks passed, but GitHub currently reports `DIRTY`; its review history contains comments rather than an approval quorum. Do not merge from the older passing checks.
- #7467 targets #7440's branch and is `CLEAN` against that parent with its replay check passing. It cannot be treated as mainline-ready until #7440 is reconciled, refreshed, and independently reviewed.

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
- The branch name/tip snapshot came from REST `repos/Unjuno/agent-interface/branches` pagination (391 records) and is retained in [BRANCH_TIPS_20261005.csv](BRANCH_TIPS_20261005.csv). The open-PR metadata is retained in [OPEN_PRS_20261005.csv](OPEN_PRS_20261005.csv). An all-branch ancestry audit did not complete in this session; **no branch is classified safe to delete**.
- Review decisions are unset for the captured open PRs, and branch protection/rulesets were absent. This means repository settings do not enforce the review gates; maintainers must respect per-PR instructions.
- The older [2026-10-01 inventory](BRANCH_INVENTORY_20261001.md) remains an immutable prior snapshot; this file supersedes its counts, not its provenance.

## Next pass

1. Export complete PR state, all reviews/comments, and commit/file lists at a single captured time.
2. Map all 391 branch tips to open, closed, and merged PRs; then compute unique commits against the relevant base and identify dependent open refs.
3. Group exact duplicate evidence publication and superseded candidates; request owner disposition for unresolved and private-resource branches.
4. Merge only individually reviewed ready PRs whose required checks pass against the current base. Record merge commit, retain the branch initially, and prune only after unique commits and evidence are verified present elsewhere.

## Additive correction and refresh — 2026-10-05 16:47 JST

The fixed CSV snapshot above records `main` at `64dcc4c677202eb9b1c9b41ff808e56486c8321f`; the prose line naming `11445a7ca200404ddc80bf7ebb1dbef86eb059de` as the API default tip at 16:24 JST is chronologically inconsistent with that CSV. The first-parent history places `11445a7` at 16:27:44 JST. Preserve the CSV as captured; read this note as the correction to the prose chronology. The later captured `9146507` (16:32:17 JST) and `380c3d2` (16:37:15 JST) advances are subsequent history, not the CSV capture tip.

A public GitHub pull-request page read around 16:47 JST showed 244 open PRs, but subsequent public HTML reads served conflicting repository pull-request counts (including 254 and 337). Treat those rendered totals as inconsistent cache/page observations, not a reliable current census. They do not expose complete review/check/base/head/dependency state and cannot classify PRs for merge or branches for deletion. At that read, fetched `main` was `c1d03aca16ba4d3ffcc6c63b907a6fc11a91be5d`; it later advanced as recorded below. `gh auth status` reports the stored GitHub token is invalid; an authenticated paginated refresh is still required.


## Snapshot-head reconciliation — 2026-10-05 17:00 JST

Using the frozen `OPEN_PRS_20261005.csv` (338 rows), fetched remote branch refs (388), and `origin/main` at `1fa854d537bfd711b5dfd99f8c04ab6c35bad286` (17:00 JST), an ancestry comparison found:

- 3 recorded head commits are ancestors of current main: #7685, #7776, and #7881. First-parent history records their merge commits at 16:47:28, 16:46:34, and 16:56:49 JST respectively. These merges happened in the repository; this audit did not merge them.
- 7 recorded head branch names were absent from the fetched remote-tracking refs.
- 4 present head branches now point to a different SHA than the snapshot.
- 324 present branches still point to the snapshot SHA, which is not an ancestor of current main.

These categories partition the 338 snapshot rows. They are historical reconciliation only; they do not prove current PR state, uniqueness of evidence, gate satisfaction, or branch deletion safety. In particular, do not infer that a row with an ancestor head has no later PR changes or unresolved review requirement from the stale CSV alone. Preserve those branches until a live PR/dependency and unique-commit audit is available.

## Complete API refresh — 2026-10-05 08:16:25Z

The earlier public HTML observation of 244 open PRs was incomplete and is superseded. Paginated GitHub REST reads captured 336 open PRs (299 draft, 37 non-draft) and 382 branches. Complete timestamped metadata snapshots are preserved in [OPEN_PRS_20261005_081625Z.csv](OPEN_PRS_20261005_081625Z.csv) and [BRANCH_TIPS_20261005_081625Z.csv](BRANCH_TIPS_20261005_081625Z.csv). All 336 unique open-PR head branch refs existed in the branch snapshot; 46 additional branches were not heads of a currently open PR and remain unclassified for deletion.

Stack map: 280 PRs targeted `main`; 56 targeted a non-main base across 36 distinct branches. Of those 56, 45 base refs matched another currently open PR head branch; only 27 child base SHAs exactly matched that parent PR current head SHA. Eleven non-main base refs had no currently open PR head mapping, and 18 mapped children were pinned to a different SHA than the parent’s current head. Preserve these stacks until their live parent/base and unique commits are reconciled.

Review-gate and check snapshot for the 37 non-draft open PRs: zero had a submitted `APPROVED` review and zero had `CHANGES_REQUESTED`; 13 had no submitted review and 24 had comment-only submissions. Five PR bodies explicitly required nonauthor approval/quorum (#8029, #7965, #7938, #7733, #7229); none had any approval. Thirty-seven head commits had check runs, all completed; three heads had at least one failed check (#7524, #7529, #7540). These runs are attached to the recorded head SHAs and do not establish that the PR base is current.

At the same capture, 28 non-draft PRs targeted `main`, and none recorded the captured `main` SHA `2e1def5886740e347dc6f4ecd4a2f158056a38dc` as its base SHA. The default branch advanced during this work: a follow-up ref read at 08:20:22Z reported `db749b182224842defd6556cc82f88ac5e6448fa` (commit time 17:18:06 JST). All 28 therefore require a fresh base and check/review epoch before merge consideration. No PR was merged or branch deleted in this audit.

## Follow-up state — 2026-10-05 08:25:39Z

A subsequent GitHub Search API read reported 328 open PRs (296 draft, 32 non-draft); paginated branch reads reported 375 branches. Default branch main was  f9fb28932226a0d12c1200f8b9215f7e89993849 (17:25:11 JST). This is later state than the fixed 08:16:25Z CSV snapshot; the CSV remains unchanged.

The first-parent history since snapshot main 2e1def5 now contains integration commits associated with PRs #7791, #7619, #7514, #7461, #7581, #7510, and #7956; it also contains PR-associated commits #8104 and #8105. These repository updates were not made by this inventory audit. The PR and branch count differences do not establish which remaining branches are safe to delete.

## Moving repository state — 2026-10-05 08:28:11Z

A further read found 326 open PRs (294 draft, 32 non-draft), 374 branches, and main at 2f7f4bda7db487386d38684fb7cab9c905d883e2. These are live counts after the 08:25:39Z state above; they are not row-by-row reconciled to the frozen 08:16:25Z CSVs.

## Moving repository state — 2026-10-05 08:31:05Z

A further Search API and branch-page read reported 328 open PRs (297 draft, 31 non-draft), 378 branches, and main at 10be950b8fb6e2799b837b541577fb5f32db858d (commit time 08:30:37Z / 17:30:37 JST). The latest main commit is the integration of PR #7887. These live totals remain separate from the 08:16:25Z fixed CSV snapshot.

## Revert-aware follow-up — 2026-10-05 08:32:24Z

At this read, GitHub reported 328 open PRs (297 draft, 31 non-draft), 376 branches, and main at 0db00a564daff64e47fd6931954ace0f71ab8f2b (08:31:48Z / 17:31:48 JST). Main first-parent history shows #7887 was merged at 17:30:37 JST and reverted by PR #8113 at 17:31:48 JST. Preserve both events; the transient merge must not be treated as an enduring integration or as grounds to delete its branch/evidence.
## Current-main follow-up — 2026-10-06

At the live read, `git ls-remote --heads origin` returned 427 remote branch refs and `main` was `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. These counts are a moving snapshot, not an atomic PR/ref census. The complete head/base dependency, ownership, and unique-commit audit remains incomplete.

Evidence rescue PR #8223, carrying the unique scorer readback A03 package from closed #7698, is now merged. Its merge commit `2976694a1dbe07ad301b785b193e9f1f5aef6f59` is an ancestor of the fetched `main`; the DOOM research index is present. The original test/source snapshots and limits remain described in the merged rescue record. No experiment or auditor was rerun during this verification.

The closed-unmerged #8195 branch remains absent from remote heads; `refs/pull/8195/head` still resolves to `907944756378c4fe09c4865a1b20bfa2a8cf721b`. The separate documentation correction PR #8220 has since merged as `d101a9489a50cc75398249f4d252f03ca1f1a8f6`, which is an ancestor of the fetched `main`; its correction and index entry are integrated. Do not infer that unrelated refs are safe to delete from these targeted checks.
## Merged #8220 source-ref cleanup — 2026-10-07

Deleted `fix/8102-frozen-fetch-instructions-20261005` at exact tip `2edb17d7c398049b5d72b7fd1363361b0fa55e6e` after confirming PR #8220 merged as `d101a9489a50cc75398249f4d252f03ca1f1a8f6` and that merge is on current `main` `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. The merged PR changed only the DOOM index and the additive correction guide: the guide blob is identical on main, and the index still contains the correction link (its whole-file blob has later additive entries). Open head/base searches returned no dependents; no worktree used the branch. After deletion, the branch head is absent and `refs/pull/8220/head` remains fetchable at the former tip. No experiment, auditor, or replay was rerun.
## Merged #8223 evidence-ref cleanup — 2026-10-07

Deleted `rescue/scorer-readback-evidence-7698-current-main-20261005` at exact tip `f788f4d168dca7602f8250b4eed6b5b0b9c51833`. PR #8223 is merged as `2976694a1dbe07ad301b785b193e9f1f5aef6f59`, an ancestor of current main. All six scorer package files have identical blob IDs at the former head and main; the DOOM index still contains the rescue entry, with later additive entries explaining its different whole-file blob. No open head/base dependents remained. The clean, agent-created rescue worktree and its stale local branch ref were removed. The source branch is absent after deletion; `refs/pull/8223/head` remains fetchable at the former tip. No experiment, test, auditor, or replay was rerun.
## Merged rescue-ref cleanup — 2026-10-07

Four merged rescue refs were removed after verifying each exact tip was an ancestor of fetched `main` `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`, each PR was closed-merged, and targeted open-PR head/base searches returned no dependents:

- #8213 `rescue/59-feedback-onset-a01-20261005` at `68f9bf84efd6a81903b8abe2b61a4cd60860aa8d` (merge `f13d088c17566f41da76960a83e9eb8f1ff4dc90`).
- #8214 `rescue/59-health-negative-control-a05-currentmain-20261005` at `fed88986678db44f91cefcddd53dac802d59f70b` (merge `c2f9515c25b2aa8045f2a2272dc0fac7354f213e`).
- #8173 `rescue/59-app-consumption-audit-lineage-main-20261005` at `ad8fbcfe60769eef342e54bd956428a515c4a02f` (merge `9af8bda3ead852955bd879301a7a2ba2f94ab629`).
- #8215 `rescue/59-app-consumption-a01-20261005` at `af2c93f410590195d1194700bcb50e15a64a9e6f` (merge `378ea2ec69aeedc0e4fbe3ce76d071fe023d4de5`). Its clean agent-created worktree and local branch were removed before deleting the remote ref.

Each remote ref was deleted with an expected-tip lease. The four closed PR pull-head refs remain fetchable at their former tips. No experiment, auditor, or replay was rerun. A separate audit kept #8227's source ref because its tip was not an ancestor of current main; no cleanup is inferred for that branch.

The latest non-atomic branch-head count after these operations was 424; ongoing concurrent updates may change it.
## Additional merged-source ref cleanup — 2026-10-07

Removed three more merged PR source refs after confirming the exact remote tip was an ancestor of fetched `main` `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`, no open PR used the branch as head or base, and no local worktree used it:

- #8245 `engineering/receipt-empty-index-20261006-r7p4` at `18be81517fd2f28848b9f497c4190d9ba7b2c4c8`.
- #8243 `research/59-8094-currentmain-delta-audit-20261006` at `a290629443f590e4ed792f20f37199e180b05f64`.
- #8247 `rescue/7223-uncertain-relay-current-main-20261006` at `401d5171c91ed90097ac2de80c7df12a9f70e0b1`.

Each ref was deleted with an expected-tip lease; closed PR pull-head refs remain fetchable. No test or experiment was rerun. The latest non-atomic remote-head count was 422 after these deletions.
## Further merged-ref cleanup — 2026-10-07

Removed two additional merged source refs after current-main ancestry, exact tip, open head/base dependencies, and worktree checks:

- #7291 `rescue/telemetry-cap-2a04-20261004` at `dd8bea5a2d38a20e728bd37faec8bae5bed0b336`.
- #8225 `fix/research-index-vision-namespace-20261006` at `d33bbacc3b6ea08ad8bd3050272c7ae95837d2f6`.

Both were deleted with expected-tip leases, and their closed pull-head refs remain available. #8224's merged PR head (`8afc43ba90c2fd37c9f4fea4a33dc06abfe50eeb`) is not an ancestor of fetched main, so retain its branch pending a separate content/history comparison. The latest non-atomic remote-head count was 421.
## Correction — #8224 source-ref disposition — 2026-10-07

The earlier hold for #8224 was based on its source tip not being an ancestor of current main. A later path-level check resolves that hold: all four changed files (`.gitattributes`, the A05 STOP report, its checksum file, and STOP record) have identical Git blob IDs at the former head `8afc43ba90c2fd37c9f4fea4a33dc06abfe50eeb` and main. PR #8224 is closed-merged; open head/base searches and the local worktree registry had no dependents. The source ref was deleted with an exact-tip lease; `refs/pull/8224/head` remains fetchable. No experiment or auditor was rerun.
## Correction — #8227 rescue-ref disposition — 2026-10-07

The earlier #8227 hold was based on its source tip not being an ancestor of current main. A complete path-level comparison resolves that hold: all eleven package/config files match main by Git blob ID, and the research-analysis index still contains the package link; the only index difference was later main-side entries absent from the old head. PR #8227 is closed-merged. Open head/base searches and the worktree registry returned no dependencies. The source ref was removed with an exact-tip lease, while `refs/pull/8227/head` remains fetchable at `ffec38c5c64ff7d6dba39576662b9f09daff0ae1`. No candidate, auditor, or experiment was rerun.
## Rescue of #8222's omitted analytical-index entry — 2026-10-07

A read-back found that merged PR #8222's unique `Issue #7799 T0 A01 pairwise eligibility` summary row was absent from current main's `research/analysis/README.md`, despite the package directory link and evidence files being present. The exact summary row from the closed PR head is now proposed in open Draft PR #8263 as a single-file, additive index repair. It preserves the `HOLD_T0_NO_ELIGIBLE_INDEPENDENT_PAIR` result and its synthetic-only limits; no package, candidate, or auditor was rerun.

After confirming #8222's only changed path was the index, its row was present in the successor branch, no open PR depended on the old ref, and no worktree used it, deleted `fix/7799-analysis-index-20261005` at exact tip `8a5417c34df33cfafe137cbb8c257199b0f68258`. The closed #8222 pull-head remains fetchable. The restored summary is proposed for review and is not yet integrated into main.
## Additional merged-ref review — 2026-10-07

Removed #8211 `research/8185-exact-transform-oracle-a02-20261005` at exact live tip `925b373c526287d9eaf7b79617565ce61fa47702`. PR #8211 is closed-merged, the exact tip is an ancestor of current main `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`, and no worktree used the branch. The remote branch is absent after deletion; `refs/pull/8211/head` remains fetchable at the former tip.

Retain #8219 `research/8157-prefix-audit-a04-20261005`. The closed merged PR records head `4ac8abf9c18af0ad4090cb1fe0c0f4d21bd89b6f`, but its live branch points to `93500f925459f7c8b05947887dc40975885e929d`. That live tip is not an ancestor of current main and differs from it across a large tree delta; prior path-equality reasoning about the recorded PR head does not establish custody of the live branch contents. Preserve the ref pending a direct unique-content and dependency audit. No experiment, auditor, or replay was rerun.

The latest non-atomic remote-head count after #8211 cleanup was 422.
