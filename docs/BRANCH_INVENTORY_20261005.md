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

## Correction — #8219 live source-ref disposition — 2026-10-07

The earlier hold on `research/8157-prefix-audit-a04-20261005` is resolved. Its live tip `93500f925459f7c8b05947887dc40975885e929d` differed from the closed merged PR #8219 recorded head `4ac8abf9c18af0ad4090cb1fe0c0f4d21bd89b6f` by the post-merge coordination-gate disclosure and a merge of then-current main. The original #8219 merge commit is an ancestor of current main, all changed package files and the added Issue #7817 evidence package match main by blob ID, and main contains the gate disclosure plus later checksum/byte-stability correction. In particular, the live branch's A05 checksum row for the unchanged `SOURCE_SHA256.txt` was stale; main's row matches the actual file bytes. No worktree used the branch and an open-PR search found no dependent. Deleted the remote ref with an expected-tip lease; `refs/pull/8219/head` remains fetchable at the recorded PR head. No experiment, auditor, or replay was rerun.

After the #8219 deletion, a non-atomic `git ls-remote --heads origin` read observed 421 refs.

## Historical #7698 custody detail carried forward from superseded #8163 — 2026-10-07

The closed, unmerged #8163 branch contained a dated record of the #7698 A03 evidence rescue: #8223 head `33ed114d7fa3775523fc9906cf67d7f26c221378`, based on main `b5be19963454ce5edafc945b78b100012952dd15`; original source ref `fix/59-scorer-readback-type-20261005` was removed at `614348df05ae603526a6a74a8feec17f039e7927`, with `refs/pull/7698/head` retained and source/test snapshots transferred to #8223. That historical note had not been copied into this current-main inventory branch. Current disposition is recorded above: #8223 merged as `2976694a1dbe07ad301b785b193e9f1f5aef6f59`, with package-file identity verified on main. The superseded inventory branch itself is now redundant; no experiment, test, or auditor was rerun.

Deleted `maintenance/inventory-followup-clean-20261005-r2` after confirming the closed-unmerged #8163 exact remote tip was `2cc24ae42ac79994e9b84fac93159427f9a99f25`, its only unique 7-line inventory addition had been carried into this branch, no open PR used it as head or base, and no worktree had the branch checked out. The exact-tip lease succeeded; the branch head is absent and `refs/pull/8163/head` remains at the former tip. A later non-atomic remote-head read observed 421 refs; concurrent updates may change this count.

## Closed #8122 source-ref cleanup — 2026-10-07

After carrying the distinct remote-tip and local-worktree historical records into this inventory, rechecked PR #8122 as closed-unmerged under the repository owner `Unjuno`, confirmed no open PR head/base dependents, and confirmed the remote source tip and closed pull-head both resolved to `3b1c12ca6ebc01101aad443c71601efbc17c85c0`. The clean local worktree remains at divergent commit `23783e605820eedbb5cdd40d1e324586f599d850` as a retained recovery copy. Deleted only remote branch `maintenance/inventory-followup-20261005` using an exact-tip lease. The source head is now absent, while `refs/pull/8122/head` remains fetchable at the former tip. A subsequent non-atomic remote-head read observed 423 branches.
## Follow-up review and current state — 2026-10-05 17:54 JST

This note supplements the frozen 08:16:25Z CSVs and the 08:32:24Z state above; it does not replace either snapshot.

- PR [#8114](https://github.com/Unjuno/agent-interface/pull/8114) merged at 08:44:43Z as `9febfe4926cde6629f9751d6444f6b802cf31328`. Its body explicitly required independent verification and asked that it remain open until that review was complete. GitHub's submitted-review endpoint returns no reviews, and its only issue comment is an automated code-review usage-limit notice. This audit independently rechecked the previously parsed snapshot totals (336 PR rows, 382 branch rows), uniqueness and exact branch-tip joins for all 336 open-PR heads, and stack arithmetic (56 non-main-base; 45 mapped to open parent heads; 27 child base SHAs equal the mapped parent head; 18 mapped but mismatched; 11 unmapped). The requested timestamp/SHA correction is consistent with commit chronology. Main history confirms #7887's merge at 17:30:37 JST and the #8113 revert at 17:31:48 JST. The content is useful as an additive historical record, but merge occurred before its stated independent-review gate was satisfied; record that as a process deviation. Do not treat the frozen CSV or stale PR counts as live branch disposition.
- Current main advanced past `0db00a564daff64e47fd6931954ace0f71ab8f2b`; API first-page history at 17:51 JST includes #8116 and #8117 after the #8114 merge. Re-fetch all PR and branch pages plus checks/reviews at one capture time before assigning close, merge, or deletion candidates. No live full census was completed in this pass.
- PRs [#7195](https://github.com/Unjuno/agent-interface/pull/7195) and [#7201](https://github.com/Unjuno/agent-interface/pull/7201) are both still draft and overlap on `research/live_control/test_native_exchange_v1.py`. #7201 changes the request-path comparison using `resolve()`; #7195 uses `resolve(strict=True)` there and changes four additional test expressions. #7201's recorded Linux run covers only its own one-line candidate and must not be counted as validation of #7195's strict candidate or four other expressions. Preserve both proposals and their recorded evidence; do not merge/close/retarget either until the owner reconciles the overlapping implementation on a fresh current-main base, completes the required exact-candidate Linux validation and independent content approvals, and records one forward application plan. A local sparse-fetch attempt for #7195 exhausted disk during this audit; its temporary linked worktree was safely removed without touching other worktrees. No test run is claimed.
- PR [#8115](https://github.com/Unjuno/agent-interface/pull/8115) is an open draft current-main rescue with one commit and 18 files. Review found 17 experiment-package Git blobs identical to the old #7453 source, plus one index link. Its description preserves the experiment's narrow fake-Xlib scope and says neither candidate nor auditor was rerun. No submitted independent review is present; keep it a candidate for review, not as accepted or integrated evidence.
- The failed sparse fetch left two Git temporary pack files totaling about 503 MiB in the local clone's object-pack directory. No Git process remained and the new worktree was removed; cleanup was not attempted because safe removal was not available through the approved command path. Avoid further fetches in this checkout until the pack state is handled safely.

No remote branches were deleted or pull requests merged, closed, or retargeted during this follow-up. The complete all-branch dependency/unique-commit audit remains outstanding; branch deletion safety is still unclassified.


## Paginated reference census — 2026-10-05 09:14 UTC

This additive snapshot was collected from GitHub REST pagination across the open pull-request and branch collections, plus the main ref. The endpoint reads overlapped and are not an atomic transaction; live state may change while pages are read.

- Main was 19a6b723e58ccfd2b8265e88659589ef9223fcc9.
- 332 open PRs were returned over four pages: 301 drafts and 31 ready. Of these, 280 target main and 52 target another branch.
- All 332 distinct open-PR head branch names were present in the 385-branch listing. The other 53 branch names are not heads of an open PR; their closed-PR, dependency, and unique-commit status was not audited here.
- Among the 52 non-main-base PRs, 46 base branch names map to another open PR head. For those 46, 28 base SHAs equal that parent PR's current head SHA and 18 differ; six base branches have no matching open-PR head.
- All 280 PRs targeting main recorded a base SHA different from the observed main tip. Treat these as potentially stale review epochs; compare each head with current main and re-check its CI before considering merge.

This is a pagination/count and branch-name stack map only. It does not inspect each PR's review requirements, CI, file overlap, closed PR history, or commit ancestry, and it does not identify any branch safe to delete. Preserve all 385 branches pending the all-branch unique-commit and dependency audit.


## Post-census integration and review-process note — 2026-10-05 09:18 UTC

This snapshot follows the merge of PR #8120 and is later than the 09:14 census above. Paginated REST reads across open PRs, remote branches, and the main ref overlapped and are not atomic.

- Main remained 19a6b723e58ccfd2b8265e88659589ef9223fcc9.
- 335 open PRs were listed: 303 drafts and 32 ready. 283 targeted main and 52 targeted another branch.
- All 335 distinct open-PR head refs appeared in the 386-branch listing. The other 51 branch names are not open-PR heads and remain unclassified.
- Of 52 non-main-base PRs, 46 base branch names map to open-PR heads: 28 base SHAs match the parent head and 18 do not; six base refs have no matching open-PR head.
- Of 283 main-target PRs, eight payloads recorded the current main SHA and 275 recorded a different SHA. This is a stale-epoch indicator, not a per-PR behind calculation; compare each head with current main and re-check CI before merge.
- PR #8123 merged at 09:00:43Z as f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c; its submitted-review endpoint is empty and its only issue comment is the code-review usage-limit notice. It preserved the WSLc setup STOP; this is an additional non-author-review process deviation.
- PR #8120 merged at 09:13:34Z as 846acff11e60093da551986583ac525452480b0c. All seven head checks passed, including Analysis Index, but the submitted-review endpoint is empty. Preserve A03 STOP, A04 HOLD, A05 result, raw data, and the scoped conclusions; record the missing non-author review separately from the scientific result.
- PR #8128 merged at 09:14:05Z as 902cbbfd8535b03af09e8f4a1bb4a4d7e73de659. The retained report explicitly says it was not independently audited and claims no method PASS or human study; the submitted-review endpoint is empty. This is another process deviation, not a change to the report's HOLD disposition.
- PR #8133 merged at 09:14:09Z as 19a6b723e58ccfd2b8265e88659589ef9223fcc9. Its submitted-review endpoint is empty. The PR body records 17/17 analysis-index tests passing and a separate mixed-suite attempt stopping because the image lacked Git; retain those limits. This is a process deviation even though the documentation change and its reported checks are scoped.

These four merges plus #8114 lack submitted non-author reviews in the GitHub review endpoint. This inventory records the process deviations; it does not reverse merges or weaken the evidence preserved by those PRs.

This remains a reference census, not a unique-commit audit. No branch is classified safe to delete.


---

## Follow-up API snapshot and evidence rescue — 2026-10-05 18:40 JST

A later authenticated GitHub Search/branch read at approximately 18:40 JST returned 335 unique OPEN PR IDs and 387 unique branch refs (current `main` at `9febfe4926cde6629f9751d6444f6b802cf31328`). The PR search was partitioned by creation-time windows to avoid its 100-result cap. Individual REST detail fetches then hit GitHub's API rate limit: only 60 of 335 PR detail records were returned. The earlier complete 336/382 CSVs remain the most recent complete head/base/branch snapshot; the 335/387 totals are counts only and do not update row-level refs, bases, draft status, review state, or checks. Do not infer that the one-count decreases identify particular PRs/branches.

During that read, the branch endpoint returned five pages totaling 387 unique names, while current open-PR search returned 335 unique PR IDs (#6934–#8148); there were no PRs created before 2026-10-03. The current ref count and PR count are not a deletion classification. Full current head/base mapping, closed-PR dependencies, unique commit/path attribution, and owner/allocation status remain unverified. No branch is classified safe to delete.

### Experiment evidence disposition

- PR [#8097](https://github.com/Unjuno/agent-interface/pull/8097) is present in current `main` via commit `ff7bfe684f5aa96e862f48c8fa44b403dc455b3b` (ancestor of `9febfe4926cde6629f9751d6444f6b802cf31328`). It rescues the V39 Xvfb A03–A08 packages, including A03/A04 STOP records, A05 invocation STOP, A06 raw plus partial audit and STOP, and A08 `PASS_METHOD_SCOPED` raw/audit. The focused current-main tests for A05 recorded 10/10 passing; they do not replace the stopped Xvfb allocations. These packages are already preserved on main; no duplicate rescue is needed.
- PR [#7980](https://github.com/Unjuno/agent-interface/pull/7980) preserves 56 X11 explicit-UP evidence files from the closed/superseded #7114 without importing its runtime fix/tests. This is evidence-only and leaves the source branch untouched.
- PR [#8114](https://github.com/Unjuno/agent-interface/pull/8114) merged the inventory errata and the 336/382 paginated snapshot. Its exact CSVs remain timestamped snapshots, not live data.

### Local recovery state

The audit workspace contains multiple retained clones/worktrees and detached review checkouts. The latest main commit `9febfe4` fixes those inventory/evidence rescues in history; older checkouts are substantially behind it and one inventory checkout contains hundreds of unrelated staged experimental paths. No such checkout was pruned, reset, or force-pushed. A partial audit clone and temp files also remain under the user's `_tmp` directory after shell-policy-denied cleanup. Re-evaluate each worktree against its owner, live PR and unique evidence before removing it.

### Next safe pass

1. Capture a fresh paginated branch-tip CSV and complete paginated PR metadata (open and closed) together with a single `main` SHA.
2. Fetch PR heads/bases in rate-limit-aware batches and verify every current head/base still resolves to the captured refs.
3. Map each branch to all PR states, dependent bases, Issue/owner/allocation, unique commits, and unique paths; keep unknown rows.
4. Preserve failed/STOP and raw outcomes, and prune only individually verified refs after their unique commits/evidence are reachable elsewhere and owners/dependents are resolved.

## Current paginated branch and open-PR counts — 2026-10-07 09:35 UTC

A fresh read observed 423 remote branch refs with `git ls-remote --heads origin`; GitHub branch search pagination also returned 423 branch names across six pages. A separately paginated search returned 359 open PRs, split by creation date to stay below its 100-result cap: 63 on October 3; 130 on October 4; 142 on October 5 (67 from 00:00–05:59 UTC, 57 from 06:00–11:59 UTC, and 18 from 12:00–23:59 UTC); 10 on October 6; and 14 on October 7. Earlier date partitions returned no open PRs.

The branch and PR reads are not an atomic snapshot, and the branch-name listing does not map refs to PR heads/bases, owners, unique commits, experiments, or active allocations. This updates backlog counts only; it classifies no branch as safe to delete. The all-ref custody audit remains incomplete.

## Fresh open-PR crosswalk and evidence-rescue cleanup — 2026-10-07 09:50 UTC

A fresh paginated GitHub REST read resolved 363 open PRs to 363 distinct head branch names and 37 distinct base names; 33 bases are also open heads, and four are base-only. The branch search and `git ls-remote --heads origin` each returned 433 refs. Therefore 66 current branch refs are neither an open PR head nor an open PR base. The reads overlapped rather than forming an atomic transaction; this set is a candidate queue only, not a deletion classification.

Closed, unmerged PR #8241's `research/reversal-geometry-20261006-g8m2` ref was removed at exact tip `b2255468f56a7e15dddaa57a1f6e74d519aba52e` after preserving its distinct allocation 02. Draft PR #8273 places the original 11 files under a separate allocation path, with all 11 Git blob IDs matching the source. The capsule SHA-256 was verified; 22 archive members were inspected without executing the helper, candidate, auditor, or tests. Allocation 01 on main remains untouched, allocation 02 remains corroborative, and the pre-freeze construction outcome remains STOP/unpooled. The closed #8241 pull-head remains fetchable at the former tip. No open PR head/base dependents or local worktree used the source branch; it was unprotected and owned by `Unjuno`.

Merged PR #8253's source-ref cleanup is also verified: `fix/ci-preview-analysis-checkout-20261006` at `0756e73a24c0f1f5ac869063b08bebe1e89dad7b` was an ancestor of main, had no open dependencies or checked-out worktree, and its closed pull-head remains fetchable.

### Remote refs outside current open-PR heads and bases

- `codex/fix-7997-evidence-wording`
- `fix/compiled-observation-exception-propagation-20261005`
- `fix/retain-unverified-x11-key-holds-20261005`
- `fix/x11-explicit-up-01a0ff2c`
- `fix/x11-wheel-ledger-01a0ff2c`
- `fix/59-a05-audit-integrity-20261005`
- `fix/59-projector-attempt-ordinal-type-e0cc-20261005`
- `fix/59-v39-admission-id-projection-a01-20261005`
- `fix/59-v39-bracket-interval-bool-20261005`
- `fix/59-v39-cover-admission-invalidation-edd067-20261004`
- `fix/59-v39-hashsafe-adapter-id-20261005`
- `fix/59-v39-raw-bracket-consistency-a01-20261004`
- `fix/59-windows-anonymous-pipe-readiness-20261005`
- `fix/7974-release-lockout-a01-20261005`
- `fix/8243-verifier-r2p6-20261006`
- `rescue/caller-terminal-journal-e01-currentmain-20261007`
- `rescue/constructor-close-fdfd-20261004`
- `rescue/cost-value-e02-currentmain-20261007`
- `rescue/gil-x11-currentmain-20261007`
- `rescue/http-edit-evidence-s07-currentmain-20261007`
- `rescue/primary-release-shape-e01-currentmain-20261007`
- `rescue/todomvc-browser-b01-currentmain-20261007`
- `rescue/wal-snapshot-6526-20261004`
- `rescue/win32-release-retain-7772-currentmain-20261007`
- `rescue/windows-reuse-causality-currentmain-20261007`
- `rescue/59-per-key-interval-a01-a02-20261005`
- `rescue/7838-a02-current-main-20261005`
- `research/cli-report-persistence-retained-p4n7-20261006`
- `research/held-chord-h7k3-20261007`
- `research/predictive-display-t0-5935-20261006-v1`
- `research/primary-uncertain-ba92-v1`
- `research/scorer-endpoint-readback-type-20261005`
- `research/strict-attempt-ordinal-v39-20261005`
- `research/v15-perkey-owner-evidence-only-20261005`
- `research/v39-attempt-ordinal-exact-int-20261005`
- `research/v39-dual-signal-epoch-a03-20261005`
- `research/v39-partial-record-drain-race-20261005`
- `research/59-cancel-release-cause-postsample-c03-20261004`
- `research/59-exact-release-trace-a01-20261005`
- `research/59-expected-key-provenance-a01-20261005`
- `research/59-owner-expiry-drain-barrier-a01-20261005`
- `research/59-per-key-release-receipts-20261005`
- `research/59-release-query-failure-probe-a01-20261005`
- `research/59-renewal-soft-stale-admission-a01-20261005`
- `research/59-v12-source-closure-20261005`
- `research/59-v39-cover-admission-main-port-a01`
- `research/59-v39-current-admission-fix-a01-20261005`
- `research/59-v39-fire-cover-ammo-audit-a01-20261005`
- `research/59-v39-frame-only-threat-a01-20261005`
- `research/59-v39-keymap-batch-a06-20261005`
- `research/59-v39-renewal-invalidation-a01-20261005`
- `research/59-v39-renewal-reject-race-a01-20261005`
- `research/59-v39-v15-cleanup-a05-current-main-20261005`
- `research/59-v39-v15-cleanup-a07-current-main-20261005`
- `research/59-xvfb-audit-v3-a02-20261005`
- `research/4435-complete-custody-20261007-k9r2`
- `research/6576-runtime-envelope-a04-20261006`
- `research/7799-pairwise-eligibility-t0-a01-20261005`
- `research/7993-superpopulation-ipcw-a02-construction-20261005`
- `research/8150-threat-profiled-runtime-eligibility-t0-20261005`
- `research/8157-prefix-audit-a03-20261005`
- `research/8185-transform-graph-a02-20261005`
- `review/7822-zero-boundary-c03-20261006`
- `test/59-feedback-before-step-bool-20261005`
- `test/59-v39-adapter-edge-cardinality-a01-20261005`
- `test/59-v39-observation-step-alias-20261005`

These 66 refs remain unclassified. Several are explicitly research/rescue branches; before deleting any, resolve closed-PR history, unique commit/path custody, active allocations, and worktree ownership. Preserve experiment raw data and STOP outcomes.


## Current open-PR crosswalk and #8217 evidence custody — 2026-10-07 09:54 UTC

After the #8217 cleanup, a fresh remote read found 434 branch refs and the complete open-PR REST collection contained 363 PRs. All 363 have distinct head refs. Thirty-seven branch names are open PR bases; 33 overlap with open heads and four are base-only. Sixty-seven refs are neither open heads nor bases. These counts and lists come from overlapping reads and remain a working snapshot, not a deletion classification.

Deleted closed-unmerged #8217's `research/7799-pairwise-eligibility-t0-a01-20261005` source ref at exact tip `165fa3e21949328606adfede46aea04681d05883`. All eight package entries, including the results subtree, match main by Git blob ID. The package directory link is present on main, and main's broader .gitattributes rule supersedes the source branch's narrower rule. The analytical summary row remains proposed on Draft PR #8263. The branch was unprotected, owned by `Unjuno`, had no open head/base dependencies or checked-out worktree, and its closed pull-head remains fetchable. No experiment, candidate, auditor, or test was rerun.

### Current refs outside open PR heads and bases

- `codex/fix-7997-evidence-wording`
- `fix/compiled-observation-exception-propagation-20261005`
- `fix/retain-unverified-x11-key-holds-20261005`
- `fix/x11-explicit-up-01a0ff2c`
- `fix/x11-wheel-ledger-01a0ff2c`
- `fix/59-a05-audit-integrity-20261005`
- `fix/59-projector-attempt-ordinal-type-e0cc-20261005`
- `fix/59-v39-admission-id-projection-a01-20261005`
- `fix/59-v39-bracket-interval-bool-20261005`
- `fix/59-v39-cover-admission-invalidation-edd067-20261004`
- `fix/59-v39-hashsafe-adapter-id-20261005`
- `fix/59-v39-raw-bracket-consistency-a01-20261004`
- `fix/59-windows-anonymous-pipe-readiness-20261005`
- `fix/7974-release-lockout-a01-20261005`
- `fix/8243-verifier-r2p6-20261006`
- `rescue/caller-terminal-journal-e01-currentmain-20261007`
- `rescue/constructor-close-fdfd-20261004`
- `rescue/cost-value-e02-currentmain-20261007`
- `rescue/gil-x11-currentmain-20261007`
- `rescue/http-edit-evidence-s07-currentmain-20261007`
- `rescue/native-three-arm-p01-currentmain-20261007`
- `rescue/primary-mint-sparse-currentmain-20261007`
- `rescue/primary-release-shape-e01-currentmain-20261007`
- `rescue/todomvc-browser-b01-currentmain-20261007`
- `rescue/wal-snapshot-6526-20261004`
- `rescue/win32-release-retain-7772-currentmain-20261007`
- `rescue/windows-reuse-causality-currentmain-20261007`
- `rescue/59-per-key-interval-a01-a02-20261005`
- `rescue/7838-a02-current-main-20261005`
- `research/cli-report-persistence-retained-p4n7-20261006`
- `research/held-chord-h7k3-20261007`
- `research/predictive-display-t0-5935-20261006-v1`
- `research/primary-uncertain-ba92-v1`
- `research/scorer-endpoint-readback-type-20261005`
- `research/strict-attempt-ordinal-v39-20261005`
- `research/v15-perkey-owner-evidence-only-20261005`
- `research/v39-attempt-ordinal-exact-int-20261005`
- `research/v39-dual-signal-epoch-a03-20261005`
- `research/v39-partial-record-drain-race-20261005`
- `research/59-cancel-release-cause-postsample-c03-20261004`
- `research/59-exact-release-trace-a01-20261005`
- `research/59-expected-key-provenance-a01-20261005`
- `research/59-owner-expiry-drain-barrier-a01-20261005`
- `research/59-per-key-release-receipts-20261005`
- `research/59-release-query-failure-probe-a01-20261005`
- `research/59-renewal-soft-stale-admission-a01-20261005`
- `research/59-v12-source-closure-20261005`
- `research/59-v39-cover-admission-main-port-a01`
- `research/59-v39-current-admission-fix-a01-20261005`
- `research/59-v39-fire-cover-ammo-audit-a01-20261005`
- `research/59-v39-frame-only-threat-a01-20261005`
- `research/59-v39-keymap-batch-a06-20261005`
- `research/59-v39-renewal-invalidation-a01-20261005`
- `research/59-v39-renewal-reject-race-a01-20261005`
- `research/59-v39-v15-cleanup-a05-current-main-20261005`
- `research/59-v39-v15-cleanup-a07-current-main-20261005`
- `research/59-xvfb-audit-v3-a02-20261005`
- `research/4435-complete-custody-20261007-k9r2`
- `research/6576-runtime-envelope-a04-20261006`
- `research/7993-superpopulation-ipcw-a02-construction-20261005`
- `research/8150-threat-profiled-runtime-eligibility-t0-20261005`
- `research/8157-prefix-audit-a03-20261005`
- `research/8185-transform-graph-a02-20261005`
- `review/7822-zero-boundary-c03-20261006`
- `test/59-feedback-before-step-bool-20261005`
- `test/59-v39-adapter-edge-cardinality-a01-20261005`
- `test/59-v39-observation-step-alias-20261005`

These 67 refs remain unclassified. Several are research/rescue branches. Resolve closed-PR history, unique commit/path custody, owner/allocation, and worktree status before any further deletion; preserve experiment raw data and STOP outcomes.

## Closed #7498 WAL rescue-ref custody — 2026-10-07 10:00 UTC

Closed-unmerged Draft PR [#7498](https://github.com/Unjuno/agent-interface/pull/7498) used `rescue/wal-snapshot-6526-20261004` at exact tip `3f542d52ff6a573e94aae9a10ff69506e2640f7b`. The 52 changed paths were the retained C03 package under `research/integration/wal_snapshot_recovery_6526_01a0ff58_c03/`; each root entry and the four directory subtrees match current `main` by Git blob/tree ID. Main also carries the later `RESCUE_20261004.md` custody note. The original closed-unmerged PR #7083 and its pull-head remain unchanged. Issue #6526 remains open; this cleanup concerns only the duplicate rescue ref, not the separate live C01/C02 work or the historical C03 STOP/audit record.

Before deletion, a complete paginated open-PR read found no head or base dependency on the rescue branch; the branch listing marked it unprotected; and `git worktree list` found no checkout of it in this shared clone. Deleted the remote ref with an expected-tip lease for `3f542d52ff6a573e94aae9a10ff69506e2640f7b`; the closed #7498 pull-head remains the historical recovery reference. No producer, candidate, auditor, test, or replay was run. Immediately after deletion, branch enumeration reported 437 heads and the paginated open-PR collection reported 364 PRs; a full head/base crosswalk was not recomputed at that capture, so these totals do not change the earlier 434/363 crosswalk snapshot above.

## #7838 duplicate-ref cleanup and hidden ownership/dependency checks — 2026-10-07 10:06 UTC

The complete paginated crosswalk at 10:07 UTC contained 441 branches and 365 open PRs: 365 distinct open heads, 37 base names (33 also heads and four base-only), and 72 refs outside open heads/bases. The removed #7838 rescue ref is absent from this snapshot.

Deleted `rescue/7838-a02-current-main-20261005` at exact tip `9f62a4427ca7369b26b08991af13b02c3d367f15`. Its 20-file A02 package under `research/doom/v39_application_consumption_conflict_audit_59_a02_20261005/` matches current main by blob/tree ID, including all nested directory trees. Closed-unmerged #7838 explicitly says its evidence was carried unchanged by merged #8173; main contains all 20 paths. The branch was unprotected, outside the complete open head/base crosswalk, had no worktree in this shared clone, and had no associated open PR. Deleted using an expected-tip lease. `refs/pull/7838/head` (`c68aec1407f7dbcf1b3011cade5cbd7063b4bcf1`) and `refs/pull/8173/head` (`ad8fbcfe60769eef342e54bd956428a515c4a02f`) remain fetchable. No experiment, candidate, auditor, or test was rerun.

Two examples show why “outside open heads/bases” remains only a candidate set. `research/4435-complete-custody-20261007-k9r2` points at merged #8173 commit `9af8bda3ead852955bd879301a7a2ba2f94ab629` (already behind current main), but the latest #4435 comment explicitly assigns that branch and a new custody path for recovery from an attached archive; retain it while the recovery is active. `rescue/constructor-close-fdfd-20261004` is not an open PR head/base, yet the commit-to-PR endpoint associates its tip with open #8175; it is a live dependency and must be retained. Both refs were left unchanged.

## #8149 duplicate-ref cleanup — 2026-10-07 10:09 UTC

Deleted `rescue/59-per-key-interval-a01-a02-20261005` at exact tip `ec44484c35075994d72b25a2ae021a91041da75d`. Its 13 A01/A02 package files and nested tree IDs match current main exactly; the package, research index entry, and reconciliation note are preserved by merged PR #8149. The associated issue and PR are closed, the branch is unprotected, it is outside open PR heads/bases, the commit-to-PR lookup found only closed-merged #8149, and no worktree in this shared clone used it. Removed with an expected-tip lease. `refs/pull/8149/head` remains fetchable at `3c60aef79d98d8e6753059ee6290afd6f29ce067`. No candidate, auditor, test, or experiment was rerun.

The complete paginated crosswalk immediately after deletion found 440 branches and 365 open PRs: 365 distinct heads, 37 base names (33 overlapping heads; four base-only), and 71 refs outside open heads/bases. This is a fresh snapshot; the 10:07 UTC crosswalk above remains the before-deletion record.

## #7993 A02 construction evidence rescue — 2026-10-07 10:14 UTC

The unclassified source ref `research/7993-superpopulation-ipcw-a02-construction-20261005` remained at exact tip `0a26e2e5802ee26fbb8198184b95856c336c7bda`; its seven package files were fetched by path and their blob IDs matched the recorded source inventory. The package is construction-only (32 × 40 synthetic assignments; 11/11 host tests in ordinary and optimized mode), with no formal allocation. Its README explicitly distinguishes the later #8045 exact-enumeration subgate.

Created open Draft PR #8276, `rescue/7993-a02-construction-custody-20261007`, directly from current main `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. The seven package files reuse the exact source blob IDs; the only other change is a curated, scope-limited link under the existing “Retained construction archives” section in `research/analysis/README.md`. Compare reports one commit ahead, zero behind, and exactly eight changed paths. No source or test code ran. The source branch remains present pending independent review; do not treat the 10:09 UTC crosswalk as updated by this operation.

## Fresh open-PR/branch crosswalk — 2026-10-07 10:17 UTC

Paginated GitHub REST reads captured [368 open PRs](OPEN_PRS_20261007_101736Z.csv) and [444 branch tips](BRANCH_TIPS_20261007_101736Z.csv). Each open PR had a distinct head branch; all 368 heads and all 37 base names existed in the branch listing. Thirty-three base names overlapped open heads and four were base-only. The [crosswalk CSV](BRANCH_CROSSWALK_20261007_101736Z.csv) classifies 72 branch refs outside open heads/bases. All 72 were unprotected at this read; that is not proof they are safe to delete. The endpoint reads were sequential but not atomic, so this is a timestamped candidate snapshot rather than a deletion authorization.

The new #8276 rescue branch is an open PR head. Its source branch `research/7993-superpopulation-ipcw-a02-construction-20261005` remains one of the 72 outside refs and is unprotected, but its evidence is not yet on main; retain it until the exact rescue package is integrated or another durable mainline custody is verified.

### Outside-ref dependency spot-check

For eight unprotected outside refs, compared each tip with current main and queried GitHub's commit-to-PR association. Three refs are exact SHA aliases of open Draft PR heads: `rescue/g12-tesseract-psm-currentmain-20261007` ↔ #7209 (`8a6e3fb…`), `rescue/local-retrieval-c01-currentmain-20261007` ↔ #7207 (`0274747…`), and `rescue/native-three-arm-p01-currentmain-20261007` ↔ #7181 (`7c88232…`). The open PR comment histories do not identify the alias names as separate active workspaces, and the shared clone has no worktree checked out at those alias refs. Their evidence is still absent from main, so retain the aliases until their owning PRs integrate; then recheck and remove duplicate refs if still unused. Five other sampled refs were ahead of main with changed evidence paths and no PR association returned for their exact tip; they remain unclassified, not deletion candidates.

## #8278 merged-ref cleanup and inventory base refresh — 2026-10-07

PR #8278 merged as `75bfe2badd49376ac33cd8a87030e7a6a3396ecf`. Its source ref `rescue/59-typed-epoch-alias-successor-20261007` was at `77ae080572a214a3e3970e04d8d798750ba97fd1`; comparison against the new main found zero changed files and showed the ref one commit behind main. The PR was closed/merged, no open PR used the ref as head or base, the 10:17 crosswalk marked it unprotected, and `git worktree list` showed no checkout. Removed the remote branch with an exact-tip lease. The merged commit and `refs/pull/8278/head` remain recoverable; no experiment or candidate was rerun.

After main advanced, merged `origin/main` (`75bfe2b…`) into this inventory branch. The merge had no conflicts and carries the new main commit as an ancestor. The last full branch/PR census remains the 10:17 UTC snapshot above; the merge and one branch deletion are subsequent events, not a newly refreshed atomic census.

## #7997 superseded wording-fix branch cleanup — 2026-10-07

Removed `codex/fix-7997-evidence-wording` at exact tip `819f2c302109d961b8f9578f12e1d81d26b12786`. Closed PR #7997 had requested that the retained package avoid implying filesystem durability; current main already contains the scope-qualified README and the additive A04 correction. After line-ending normalization, both text files match main exactly. The branch manifest differs only in hashes for those text files and the parent `research/doom/README.md`; main's manifest reflects its current bytes. GitHub comparison showed no other changed paths, the branch tip had no associated PR, no open PR used it as head/base, the branch was unprotected, and the shared clone had no checkout. Deleted with an exact-tip lease. The original result/raw files were not run or changed; no candidate or auditor was rerun.

## #8277 main advancement and #8276 rescue refresh — 2026-10-07 10:28 UTC

Main advanced to `25accb67cca07229505bd4940e0d4c0785c6d47e` when #8277 merged. This inventory branch includes that main commit as an ancestor. The #8276 rescue branch was also advanced with latest main as first parent and its prior rescue head as second parent. Its analytical index was rebuilt from the latest main version (including #8277's generated-index update) before reinserting the curated construction entry. All seven source package blob IDs still match exactly. Compare now reports three commits ahead, zero behind, and exactly eight changed paths. No source or test code ran; #8276 remains Draft without approval or merge.

After #8277 merged, removed `rescue/5156-timestamp-order-successor-20261007` at exact tip `b594483eb6904fa3c38fd6fff742d5e66b0b37d9`. Current main comparison found the branch one commit behind with no changed files; closed/merged #8277 was its only identified PR association, no open PR used it as head/base, the 10:17 crosswalk marked it unprotected, and no worktree checked it out. Deleted with an exact-tip lease. `refs/pull/8277/head` remains at the former tip. No candidate or auditor was rerun.

## #8281 main advancement and #8276 rescue refresh — 2026-10-07 10:40 UTC

Main advanced through merged PR #8281 to `9f49b75e72e4dc0596dbfcf2bc7beb7af72652ec`. This inventory branch now includes that main commit as an ancestor. The full PR/branch crosswalk remains the historical 10:17 UTC snapshot above; no fresh full census was taken, and the counts must not be treated as current.

Refreshed open Draft PR #8276 on current main. Its commit has current main as first parent and the prior rescue tip `c7e303034eccac029f86d091ff3daf2d41ccc316` as second parent. The analytical index retains the current-main generated #7712 directory entry and the curated #7993 construction entry. All seven original #7993 package blob IDs remain unchanged. Compare against current main reports four commits ahead, zero behind, and exactly eight changed paths (the index plus seven evidence files). No package, candidate, auditor, or test code ran; no formal allocation was consumed or repeated.

Updated the #8226 and #8276 Draft PR descriptions with the current base and snapshot limitations. The merged #8281 source ref `rescue/7712-pid-boundary-successor-20261007` was not deleted: protection status and a fresh complete dependency/worktree check were not available in this pass. Retain it pending those checks. No experiment or formal allocation was run.

## #8281 duplicate source-ref cleanup and fresh counts — 2026-10-07 10:43 UTC

Removed `rescue/7712-pid-boundary-successor-20261007` at exact tip `cfb8e1f8a707cbfdb2f28fe11e43ab3bda575eb4` with a force-with-lease expected-tip check. The branch API marked it unprotected; its tip is one commit behind current main with zero changed files, its commit is an ancestor of main, its #7712 evidence directory matches main, the complete paginated open-PR read found no head/base dependency, and `git worktree list` found no checkout in this shared clone. The merged PR #8281 pull-head remains recoverable. No experiment or auditor was rerun.

A fresh sequential paginated read immediately after deletion found 368 open PRs and 442 branch refs: 368 distinct open heads, 37 distinct bases (33 overlapping heads, four base-only), and 70 refs outside those sets. All open head/base names were present in the branch listing; all 70 outside refs were unprotected at capture. These are timestamped inventory counts, not blanket deletion authorization; owner, evidence custody, associated closed PRs, and worktree status still need per-ref checks. The underlying CSVs remain the 10:17 UTC historical snapshot and were not relabeled as current.

## #8157 merged-evidence branch cleanup — 2026-10-07 10:44 UTC

Removed `research/8157-prefix-audit-a03-20261005` at exact tip `1b35587cdab8d7419eccc43a4dae76d98ef94288` with an expected-tip lease. Its branch was unprotected and outside open PR heads/bases; current main comparison showed it 117 commits behind with zero changed files, and the tip was already an ancestor of main. No worktree in this shared clone used it. Commit-to-PR association showed merged #8219; the #8157 Issue comment confirms its A02/A03/A04/A05 result and STOP records were retained on main, without reruns or relabeling. The issue remains open because the TTC method comparison is still unscorable. The closed pull-head remains recoverable. No candidate, auditor, or experiment was run.

A fresh paginated read after deletion found 368 open PRs and 441 branches: 368 distinct heads, 37 bases (33 overlapping heads and four base-only), and 69 refs outside those sets. All head/base names existed in the branch listing; all 69 outside refs were unprotected. The remaining outside refs still require individual custody and dependency checks; this count is not authorization to delete them.

## #8269 main advancement and merged-ref cleanup — 2026-10-07 10:48 UTC

Main advanced to `3dba6c86f212c37a2d80c844b816c38921a42cc5` through merged PR #8269. Merged latest main into the inventory branch. PR #8276 was refreshed with current main as first parent and its prior head `f5fde33c90048ad5fd9fed79fa12bbb8c8b431a9` as second parent; its seven #7993 package blob IDs remain exact, and comparison reports five commits ahead, zero behind, and exactly eight changed paths. No source, candidate, auditor, or test code ran; #8276 remains Draft pending independent review.

Removed merged source ref `research/59-v13-measurement-publication-custody-20261007` at exact tip `9f7a4a96847ee29787a87f6fb238e71da112712c` using an expected-tip lease. It was unprotected, nine commits behind current main with zero changed files, associated only with merged PR #8269, absent from all open PR heads/bases, and unused by a worktree in this shared clone. Its closed PR pull-head remains recoverable. No experiment or auditor was rerun.

The fresh paginated census after this deletion (2026-10-07 10:50 UTC) found 367 open PRs and 440 branches: 367 distinct heads, 37 bases (33 overlapping heads and four base-only), and 69 refs outside those sets. All open head/base names existed in the branch listing, and all 69 outside refs were unprotected at capture. The read is timestamped and sequential, not atomic or blanket deletion authorization.

## #6576 A04 evidence rescue Draft PR — 2026-10-07 10:57 UTC

Created Draft PR [#8284](https://github.com/Unjuno/agent-interface/pull/8284) from `rescue/6576-runtime-envelope-a04-custody-20261007`, based on current main `3dba6c86f212c37a2d80c844b816c38921a42cc5` and preserving the original source branch tip `26297fd212179493743aedfa65ba90f81351f94d` as a second parent. The 16 package files under `research/analysis/extreme_tail_eligibility_6576_construction_v1/runtime_envelope_a04_20261006/` were copied by exact blob ID; a scope-limited row was added to the curated analysis index. Compare reports 22 commits ahead, zero behind, and exactly 17 changed paths. The PR is Draft and mergeable; no review or merge is claimed.

The preserved first outcome is `PASS_RUNTIME_ENVELOPE_INVALIDATION_A04_SCOPED`, based on 90 synthetic streams with 22/30 preregistered counterexamples. Material evidence limit: the 2,925,419-byte original `formal/RAW.jsonl` is not in the source branch or PR. The package retains its SHA-256 and says `remote_raw_complete=false`; this task's workspace/attachment search found no recoverable copy. The PR states this explicitly and does not present the raw as uploaded. No candidate, auditor, controls, test, or experiment was rerun. Keep the original `research/6576-runtime-envelope-a04-20261006` branch until the reviewer decides whether this incomplete raw delivery is sufficient for main.

The fresh paginated census after opening #8284 (2026-10-07 10:57 UTC) found 368 open PRs and 441 branches: 368 distinct heads, 37 bases (33 overlapping heads and four base-only), and 69 refs outside those sets. All open head/base names existed in the branch list; all 69 outside refs were unprotected at capture. The old CSV files remain historical, and these counts do not authorize bulk deletion.

## Three exact alias-ref cleanups — 2026-10-07 11:03 UTC

Deleted `rescue/g12-tesseract-psm-currentmain-20261007`, `rescue/local-retrieval-c01-currentmain-20261007`, and `rescue/native-three-arm-p01-currentmain-20261007`. Each ref was an exact SHA alias of an open Draft PR head (#7209, #7207, and #7181 respectively); the original PR heads remain. Before deletion, the refs were unprotected, absent as head/base names in the full paginated open-PR crosswalk, unmentioned in the corresponding PR comment histories, and unused by a worktree in the shared clone. Removed each with an expected-tip `--force-with-lease`. This is duplicate-ref cleanup only; no evidence package was removed, and no experiment, candidate, auditor, or test was run. These deletions occurred after the 10:57 census and do not update its counts.

## #59 paired-epoch A03 precursor preservation branch — 2026-10-07 11:05 UTC

Fetched remote branch `rescue/59-paired-epoch-a03-precursor-20261007` at `515a1fb88217551e4c675ea648264a43ff227946`; its parents are current main `3dba6c86f212c37a2d80c844b816c38921a42cc5` and original source tip `1665dff09fca6d367e41d469492935604c65f0fd` (`research/v39-dual-signal-epoch-a03-20261005`). The compare against main has exactly ten changed paths: nine original package files with their recorded blob IDs, plus one curated row in `research/doom/README.md`. The row labels the package as a superseded seven-case precursor and says the later ten-case paired-guard result remains canonical. Its unique `a02_split_epoch_control` records that separate A02 per-signal guards preserve a split-epoch pair. The source README claims an independent raw audit, but no separate auditor stdout artifact is included; no candidate, auditor, or test was rerun in this rescue work.

GitHub CLI/API authentication was unavailable at this check, so a Draft PR could not be created or its PR state verified. The rescue branch exists remotely, but keep both the original source ref and rescue ref pending independent review and durable integration; do not treat the branch as reviewed or merged. No formal allocation or live/controller/game claim is made. No fresh full census was performed after the three alias deletions; the CSVs remain the historical 10:17 UTC snapshot and the count paragraph above remains the last verified full census.

## Main refresh after #8284 snapshot — 2026-10-07 11:12 UTC

Fetched and merged remote `main` at `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`; this inventory branch now has that exact main tip as its second parent. The merge is a source-history refresh only. It does not refresh the open-PR/branch census: anonymous GitHub REST reads returned 403 rate-limit exceeded, and `gh auth status` reports no authenticated host. The last full census remains 10:57 UTC. No PR metadata, review state, branch protection, or current ref count is inferred from the new main read.
