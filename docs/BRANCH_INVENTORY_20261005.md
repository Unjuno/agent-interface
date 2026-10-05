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

## Follow-up API snapshot and evidence rescue — 2026-10-05 18:40 JST

A later authenticated GitHub Search/branch read at approximately 18:40 JST returned 335 unique OPEN PR IDs and 387 unique branch refs (current `main` at `9febfe4926cde6629f9751d6444f6b802cf31328`). The PR search was partitioned by creation-time windows to avoid its 100-result cap. Individual REST detail fetches then hit GitHub's API rate limit: only 60 of 335 PR detail records were returned. The earlier complete 336/382 CSVs remain the most recent complete head/base/branch snapshot; the 335/387 totals are counts only and do not update row-level refs, bases, draft status, review state, or checks. Do not infer that the one-count decreases identify particular PRs/branches.

During that read, the branch endpoint returned five pages totaling 387 unique names, while current open-PR search returned 335 unique PR IDs (#6934–#8148); there were no PRs created before 2026-10-03. The current ref count and PR count are not a deletion classification. Full current head/base mapping, closed-PR dependencies, unique commit/path attribution, and owner/allocation status remain unverified. No branch is classified safe to delete.

### Experiment evidence disposition

- PR [#8097](https://github.com/Unjuno/agent-interface/pull/8097) was present in `main` at `9febfe4926cde6629f9751d6444f6b802cf31328). It rescues the V39 Xvfb A03–A08 packages, including A03/A04 STOP records, A05 invocation STOP, A06 raw plus partial audit and STOP, and A08 `PASS_METHOD_SCOPED` raw/audit. The focused current-main tests for A05 recorded 10/10 passing; they do not replace the stopped Xvfb allocations. These packages were already preserved on main at that snapshot; no duplicate rescue was needed.
- PR [#7980](https://github.com/Unjuno/agent-interface/pull/7980) preserved 56 X11 explicit-UP evidence files from the closed/superseded #7114 without importing its runtime fix/tests. This is evidence-only and left the source branch untouched.
- PR [#8114](https://github.com/Unjuno/agent-interface/pull/8114) merged the inventory errata and the 336/382 paginated snapshot. Its exact CSVs remain timestamped snapshots, not live data.

## Current reference census — 2026-10-05 10:56 UTC

This is a later, non-atomic read; branch refs, PR search windows, and `main` were observed through separate requests. Main was `fd4f9e4533aa5baa5952e89cd830c98b26e7c537` when the ref was read.

- Partitioned GitHub Search returned 332 unique open PR IDs; a separate query found none created before 2026-10-03.
- `git ls-remote --heads` returned 395 branch refs with 395 distinct tip SHAs.
- A join of open pull-request head SHAs to repository branch-tip SHAs matched 331 branch tips. The other 63 non-main branch refs do not match an open PR head tip at this read.
- The unmatched refs are not deletion candidates by count alone. Closed/merged PR relationships, dependent branches, unique commits/evidence paths, and owner/allocation status remain to be audited. No branch is classified safe to delete.


## Audited branch cleanup — 2026-10-05 11:12 UTC

Remote branch `maintenance/inventory-followup-clean-20261005` was deleted after an individual audit:

- Its sole PR, #8145, was closed unmerged and superseded by #8163. No PR used the branch as a base.
- The four commits unique to that branch relative to current main changed only this inventory document. The full document content is present in this successor PR, with later census updates.
- After refreshing remote-tracking refs, no other repository branch contained the branch tip. No local worktree used this branch.
- The branch tip remains reachable from closed PR #8145's head ref `a4fed4179db89c07ca2d89ab7f8ead7e5ca9d20c`; that PR ref was verified after deletion.

The exact branch ref is absent after deletion. The subsequent branch-list read still returned 399 refs, so aggregate counts remain sensitive to concurrent repository updates and were not used as deletion evidence. The separately checked-out `maintenance/inventory-followup-20261005` branch and its local-only commit were retained.


## Individually audited branch dispositions — 2026-10-05 11:22 UTC

The following refs were reconciled individually. The GitHub page reads overlapped with active repository updates, so aggregate branch/PR counts are intentionally omitted as deletion evidence.

- **Deleted merged branch** `research/7411-user-worthwhile-benefit-a01-20261004`, tip `be7df5c03103e3327842214e933ed1ac01fe5226`. PR #7592 is merged at `fd4f9e4533aa5baa5952e89cd830c98b26e7c537`, which remains an ancestor of current main `3c2254ddc4446bec9a8ab4871ed05defa0a900f9`. All 17 paths added by that PR were checked against current main and have identical Git blob IDs. No open PR used the branch as a head or base, and no worktree used it. After branch deletion, the original PR head remained fetchable. Preserve the formal disposition `HOLD_AUDIT_INCOMPLETE`; the post-hoc verifier does not replace the preregistered gate.
- **Deleted merged branch** `research/8150-t0-current-main-sync-20261005`, tip `f428e97a062a0615f8bf6485108619b299b1d1f5`. PR #8167 is merged at `21fecd58b9de30073c97234124e73b78c67d4b0c`, an ancestor of current main. The merge commit records the nine PR paths; the original closed-PR head remained fetchable after branch deletion. No open PR used the branch as a head or base, and no worktree used it. The preserved result is `HOLD_REVIEW_DISAGREEMENT`, not a runtime eligibility PASS.
- **Deleted superseded rescue branch** `rescue/journal-wire-6042-20261004`, tip `77df97fb23a7093172a2109e0768d86df7c6c1f6`. Closed-unmerged PR #7298 names Draft PR #7509 as its successor. All seven paths changed by #7298 were verified byte-for-byte by Git blob identity in #7509 (head `b32e8d5e1e6a411643369ed59e4fcfc605fe658c`). No open PR used the old branch as a head or base, and no worktree used it. The old PR head remained fetchable after deletion. #7509 remains open and unmerged, so the evidence is preserved for review rather than counted as integrated into main.

These were per-ref dispositions, not a complete all-branch audit. Other non-head refs still require their own closed-PR, dependency, unique-commit/evidence, worktree, and owner review. A later audit found merged PR #7974's branch still checked out; it was retained.

## Paginated branch/head census — 2026-10-05 11:39 UTC

This is a non-atomic, read-only API snapshot. The `main` ref was `1fbef34f244588bff3d79b7cbea423dcb510ef8f` when queried.

- Paginated branch reads returned 397 refs across page sizes 100, 100, 100, and 97.
- Paginated open-PR reads returned 326 PRs across page sizes 100, 100, 100, and 26. Their 326 head ref names were unique.
- 71 branch refs had no matching open-PR head name. This is a head-only join; it does not check open PR base refs or prove that a branch is unused.
- The 500 most recently updated closed PR records included a same-name head for 65 of those refs: 3 had at least one merged PR and 62 were associated only with closed-unmerged PRs. Four current branch tips did not match any same-name closed-PR head in that retrieved set. The six refs without a match include `main` and five other refs; because the closed-PR query was limited to its latest 500 records, lack of a match is not proof that a branch has no PR history.
- No ref was deleted based on this count. The previous note that #7974's branch is checked out remains a concrete reason to retain it; the other 70 refs still need individual dependency, unique-commit/evidence, worktree, and owner checks before any disposition.
- The available GitHub connector exposes branch reads and ref updates, but no branch-delete operation. Do not emulate deletion by moving a ref.

Counts can change while requests are paginated. These numbers are a navigation aid, not a deletion criterion or an atomic before/after comparison.

## Individual provenance check — #8092 A01 branch — 2026-10-05 11:46 UTC

Branch `research/8068-imperfect-repair-t0-a01-20261005` currently points to `c3cdedfe68ef4adb240d5ab5313b8285c9140d9f`. Closed unmerged PR [#8092](https://github.com/Unjuno/agent-interface/pull/8092) and its correction comment classify A01 as a redundant, noncanonical allocation: PR #8076 had already completed the finite imperfect-repair method question and a targeted T1 HOLD. The correction explicitly says the A01 raw, WSLc candidate STOP, and audit remain unmodified for transparent provenance, and says not to merge #8092 or treat it as a successor result.

A current comparison to `main` shows 10 A01 packet files plus the analytical index entry absent from main. The package records its separate 12-cell host method check and one WSLc candidate output-path STOP; its independent WSLc audit was over the existing host raw and does not establish a WSLc candidate pass. The canonical later #8068 T0/T1 package on main answers a different seven-cycle fixture and retains `HOLD_NO_IDENTIFIABLE_REPAIR_HISTORY`.

Disposition: retain this ref and closed PR head as the transparent provenance copy; do not promote it as new Issue-level evidence or delete it while its raw/STOP/audit are only present there. This is a per-ref custody finding, not a branch deletion authorization or a general classification of unmatched refs.


## Individually audited branch cleanup — #7308 — 2026-10-05 11:43 UTC

- Deleted remote branch `fix/grounding-failure-accounting-6178-20261004`, tip `8b00b4ba0774efdc5d29d9ccecd88d1d70c0fcf5`. Closed-unmerged PR #7308 was explicitly superseded by #7521.
- The two paths changed by #7308 were audited against its stacked base: the added regression file is byte-identical in #7521, and the ineligible-result accounting block in `research/live_control/integrated_efficiency_app_server_model_v1.py` is byte-identical in the successor. #7521 also registers the test in `runtime/integration_checks/native.py`.
- No open PR used the old branch as a head or base; no local worktree used it. After deleting the branch, the old #7308 head remained fetchable from the closed-PR ref.
- Successor #7521 remains open Draft on main `1fbef34f244588bff3d79b7cbea423dcb510ef8f`. The focused fake-client tests and earlier failing full macOS run are historical; no tests were rerun during refresh. Required fresh checks and nonauthor review remain pending.

This is one individually audited disposition after the 11:39 census, not a classification of the remaining non-head refs.


## Individually audited merged-branch cleanup — 2026-10-05 12:05 UTC

Two remaining merged PR branches were deleted after per-ref checks:

- `rescue/59-per-key-interval-clean-20261005`, PR #8149, head `3c60aef79d98d8e6753059ee6290afd6f29ce067`, merged as `7e79b4d5fa02d4877f5c53c7f6f234f181e7a5cd). The merge commit is an ancestor of main `95316efef54b092fc2f0264539223830cdb9ba21`; all 15 PR changed-file blobs match main exactly.
- `research/7367-frozen-audit-binding-a02-20261005`, PR #8184, head/PR commit `c9aad08642bd1472517ab03ea3675237acecd1c1`, merged as current main `95316efef54b092fc2f0264539223830cdb9ba21). All 13 PR changed-file blobs match main exactly.

At the final pre-deletion read neither branch was an open PR head or base, and the local worktree list contained neither branch. After deletion, branch search returned no branch for either name; `refs/pull/8149/head` and `refs/pull/8184/head` remained fetchable at their recorded tips. This is an individual cleanup record; the remaining branch audit is incomplete.


## Concurrent integration note — 2026-10-05 12:06–12:08 UTC

Main advanced from `95316efef54b092fc2f0264539223830cdb9ba21` to `4ce8558216f3e997c23359d3ec1c0646cc03ade1` through PR #8188 while this inventory was being refreshed. This was a concurrent merge, not an action by this cleanup pass. Immediately before the merge, the fetched PR body explicitly required independent nonauthor review before integration; the review-submission endpoint returned no reviews, and the combined-status endpoint returned no status entries for head `00f8708f5bd8f8325b92c724be0a3288da3a2a63`. The post-merge PR body no longer includes that gate. The merged evidence package remains on main; this note records the review-gate discrepancy and does not alter or relabel its evidence.

The current inventory branch head at the time of this check was `65560586b1551500bdb30c6d391e5d6ad3f4ee1b`, based on main `95316efef54b092fc2f0264539223830cdb9ba21` with its prior inventory head retained as a parent. Current main has since advanced by the #8188 merge; refresh again before any later merge or branch action. The full all-ref ownership/dependency audit remains incomplete.


## Concurrent integration note — 2026-10-05 12:10 UTC

Main advanced to `0c70aff144af3515835c7c6069154fc94ad55ad4` through PR #8182 while this inventory update was in progress. The merge was concurrent, not performed by this cleanup pass. After merge, the review-submission endpoint returned no reviews and the combined-status endpoint returned no status entries for head `ce544d77bdef13692ee0be6ef6fb2e0ef1eaeb11`. The fetched PR body scoped the result to a finite synthetic job-identity input boundary and did not state an independent-approval requirement. Its evidence remains on main; no broader scheduler or runtime claim is inferred.


## Individually audited duplicate rescue branch — #8170 — 2026-10-05 12:13 UTC

Deleted remote branch `rescue/59-app-consumption-a01-evidence-main-20261005-r1`, tip `b109775c3849c9a0149d12d8d13665c0e12c65b4`, after auditing its closed-unmerged PR #8170:

- #8170's description identifies open Draft #8173 as the successor and says the source package contains 26 evidence-only files, with no runtime or test-source changes.
- All 26 #8170 changed-file blob IDs were compared with #8173's 127-file proposal; every blob is identical. #8173 remains open Draft pending independent review and is not integrated into main.
- The old branch was not referenced as an open PR head/base and had no local worktree. After deleting the branch, closed-PR ref `refs/pull/8170/head` remained fetchable at the audited tip.
- The raw outputs, source snapshots, and manifest are therefore preserved in the successor proposal while original PR history remains retrievable.

This is a duplicate-branch disposition only; it does not classify remaining refs or satisfy #8173's review gate.


## Individually audited merged research-branch cleanup — #8182 — 2026-10-05 12:16 UTC

Deleted remote branch `research/7748-duplicate-id-a01-20261005` at exact tip `ce544d77bdef13692ee0be6ef6fb2e0ef1eaeb11` after rechecking all 332 open PRs and all 401 branch refs immediately before deletion:

- PR #8182 is merged as `0c70aff144af3515835c7c6069154fc94ad55ad4`; main is now `2c1c90c80389dc6aab6a950c7058528272979f2d`. Comparing the old branch tip to main showed main 5 commits ahead and no branch-only commits.
- None of the 332 open PRs used the branch as a head or base. The exact branch tip still matched #8182's head SHA; branch protection was false. The local worktree list contained no worktree on that branch.
- All 47 changed paths were checked by Git blob ID. Forty-six blobs match exactly. `research/analysis/README.md` has later additive changes on main; both #8182 A01/A02 result rows and both package index entries are present there with the same text as the old branch.
- Deleted with an exact expected-tip lease. The branch ref now returns 404; `refs/pull/8182/head` remains fetchable at the same commit, preserving review/history access.

This is one individually verified merged-branch cleanup; it does not classify the other non-open-PR refs. No tests or experiments were run.


## Individually audited merged-branch cleanup — #8188 — 2026-10-05 12:19 UTC

Deleted remote branch `research/v39-renewal-stale-sequence-preservation-20261005` at exact tip `00f8708f5bd8f8325b92c724be0a3288da3a2a63` after verifying:

- PR #8188 is merged as `4ce8558216f3e997c23359d3ec1c0646cc03ade1`; current main `2c1c90c80389dc6aab6a950c7058528272979f2d` is four commits ahead with no branch-only commits.
- All 51 PR changed-path blob IDs match current main exactly. No open PR references the branch as head or base, and the local worktree list contains no worktree on it.
- The pre-merge review gate discrepancy for #8188 is recorded above. The content is preserved on main; deleting the merged source branch does not imply that the gate was satisfied.
- Deletion used an exact expected-tip lease. The branch ref now returns 404; `refs/pull/8188/head` remains fetchable at the audited tip.

This is a branch-ref cleanup only; it does not revise #8188's evidence or gate history. No test or experiment was run.


## Hold — merged PR #8102 source-branch history — 2026-10-05 12:20 UTC

Keep `research/59-v15-owner-evidence-current-main-20261005` at `8f5beb06d99eed093176c37a74f3620511f984fc` for now. PR #8102 is merged as `2c1c90c80389dc6aab6a950c7058528272979f2d`, but compare from the branch to current main is diverged: 20 branch-only commits and 5 main-only commits after merge base `95316efef54b092fc2f0264539223830cdb9ba21`. The PR changes 103 paths. No open PR currently uses the branch as a head or base, and the local worktree list has no checkout on it, but its unique intermediate history has not been reconciled against a preserved successor. The closed-PR head ref remains the recovery source.

The only submitted review is state `COMMENTED` by login `Unjuno`; it is not an approval. Its technical body flags the mutable fetch followed by an exact-SHA guard as a reproduction defect and explicitly does not claim nonauthor quorum or application authorization. Keep this history held until the finding and unique commit lineage are accounted for. No new candidate was rerun.


## Concurrent integration note — PR #8191 — 2026-10-05 12:25 UTC

Main advanced to `307b9e2f0420f130e9d933c037cac78501d2e547` through merged PR #8191 while the inventory was being refreshed. This was concurrent, not a merge by this cleanup pass. The fetched post-merge PR body says its preliminary `NO_INCREMENTAL_VALUE_SCOPED` conclusion is withdrawn because the “All restores visibility” clause lacked visible-ID observations; candidate/auditor each ran once and retries were zero. The review-submission and combined-status endpoints returned no entries. The PR body does not specify independent-review or approval as an integration gate. Preserve the qualified outcome; do not infer an A02 PASS or wider claim. Issue #8088 remains active in the sense that a successor needs explicit Active/All observations and the preserved-records-but-still-filtered control.


## Current remote-ref snapshot — 2026-10-05 12:25 UTC

Paginated GitHub REST reads observed main `307b9e2f0420f130e9d933c037cac78501d2e547`, **403 branch refs**, and **336 open PRs** (310 Draft, 26 Ready). Every open PR head ref exists and matches its branch-tip SHA (**336/336**). The branch partition is main (1) + open-PR heads (336) + refs not used as open-PR heads (66). The reads are non-atomic; counts and names are not deletion grounds. The previously audited merged refs #8182 and #8188 are absent. These 66 refs still need per-ref review of PR history, commit ancestry, content custody, dependencies, and owner/worktree use:

| Ref | Tip SHA | Current disposition |
| --- | --- | --- |
| `codex/fix-7997-evidence-wording` | `819f2c302109d961b8f9578f12e1d81d26b12786` | unclassified |
| `fix/compiled-observation-exception-propagation-20261005` | `68a5f26670f359bd5085dd47ccfcb43ce2c74151` | unclassified |
| `fix/retain-unverified-x11-key-holds-20261005` | `416846ef59b08c862cca84c128d1853e16a6143a` | unclassified |
| `fix/scorer-endpoint-read-type-7685-a01` | `fc8d12f13519811491015f4e2ecdd847246c55d4` | unclassified |
| `fix/x11-explicit-up-01a0ff2c` | `64b143a78f23d3e9acb229300eb195fcaf66851e` | unclassified |
| `fix/x11-wheel-ledger-01a0ff2c` | `ed7bb24e45fac16114e1247e00c8ed86cebda5c8` | unclassified |
| `fix/59-a05-audit-integrity-20261005` | `0dcd3abb9ce99b6a3f596277f124e304ed62a5fc` | unclassified |
| `fix/59-feedback-step-bool-identity-20261005` | `2bebf57d9eb617bb20ef4fbbfa6ad13f1a4ba5f0` | unclassified |
| `fix/59-projector-attempt-ordinal-type-e0cc-20261005` | `6be323b3f3ccb7c94f2bd684864e246eab8e6914` | unclassified |
| `fix/59-scorer-readback-type-20261005` | `614348df05ae603526a6a74a8feec17f039e7927` | unclassified |
| `fix/59-v15-per-key-keyup-retry-a01-20261005` | `23aa99031d7e0178de5f69f6df8e89fb63b1d9a6` | unclassified |
| `fix/59-v39-admission-id-projection-a01-20261005` | `191ba71fbfc339cd57e80bcf69dfcc856e6a2feb` | unclassified |
| `fix/59-v39-app-consumption-contradiction-20261005` | `efb712b1aa6f01d67ed119b266ef479645cfb96a` | unclassified |
| `fix/59-v39-app-consumption-sample-depth-a01-20261005` | `826329b2ff0adf0bd963c26c5b4ced2ec3fc69cb` | unclassified |
| `fix/59-v39-bracket-interval-bool-20261005` | `a427bdf9c2e76f8cc905946aa8b08f0ed26597cc` | unclassified |
| `fix/59-v39-cover-admission-invalidation-edd067-20261004` | `763ff69a531eb47a6a3f033f56171dffc80afa23` | unclassified |
| `fix/59-v39-hashsafe-adapter-id-20261005` | `40c056e322b39bbb11cb0d02aec7d8edf66367aa` | unclassified |
| `fix/59-v39-raw-bracket-consistency-a01-20261004` | `971234f7a186960cbd519c655beccbab42854a67` | unclassified |
| `fix/59-v39-typed-state-feedback-20261004` | `8bfe24520490e2bf2c6ef0288edf3e1f3c03a65a` | unclassified |
| `fix/59-wheel-release-ledger-20261005` | `e14c8267854e24e5978767cd53065622abdee3f6` | unclassified |
| `fix/59-windows-anonymous-pipe-readiness-20261005` | `67905decc40a468b9dfe45ecfbcc8a6b83999689` | unclassified |
| `fix/7849-preflight-cleanup-result-20261005` | `979e9a57db800e8f5c63ce0810c3228346e2be3b` | unclassified |
| `fix/7974-release-lockout-a01-20261005` | `5d18a471c9463a660d97e24eed9c2f863ff55bd6` | unclassified |
| `maintenance/inventory-followup-20261005` | `3b1c12ca6ebc01101aad443c71601efbc17c85c0` | unclassified |
| `rescue/constructor-close-fdfd-20261004` | `203cd69ad14aea0a05d5600ee9ace177578b51d5` | unclassified |
| `rescue/todomvc-route-b714-20261004` | `004174810fdb8cb93b95f052ebf1a764f0e64478` | unclassified |
| `rescue/59-per-key-interval-a01-a02-20261005` | `ec44484c35075994d72b25a2ae021a91041da75d` | unclassified |
| `research/scorer-endpoint-readback-type-20261005` | `39bf575ccf0c4795a0a81d06baf08e1a36a2d114` | unclassified |
| `research/spec-diversity-8088-t0-a02-20261005` | `2c1c90c80389dc6aab6a950c7058528272979f2d` | hold: Issue #8088 audit correction; #8191 successor note |
| `research/strict-attempt-ordinal-v39-20261005` | `4d79f5b97d0c467d7af62046cdfcf1af69754252` | unclassified |
| `research/v15-perkey-owner-evidence-only-20261005` | `0758b536b7b02265c8375ef70bc6703dcee77bc9` | unclassified |
| `research/v39-attempt-ordinal-exact-int-20261005` | `c405b129e83c613e815160f841070ed68267be1d` | unclassified |
| `research/v39-dual-signal-epoch-a03-20261005` | `1665dff09fca6d367e41d469492935604c65f0fd` | unclassified |
| `research/v39-partial-record-drain-race-20261005` | `d76e9945bce4b6ef0b8df79fbabf1b8ee5516815` | unclassified |
| `research/59-audit-readonly-v2-20261005` | `f191772c48fc9dfd8f33760e2b6a243b890b4a38` | unclassified |
| `research/59-cancel-release-cause-postsample-c03-20261004` | `e101c63ac4938ed4017e3021338ebd1c333d8c29` | unclassified |
| `research/59-effect-identity-join-a01-20261005` | `b9dbe5f6f4086b402e3ce23c347d38fe155d5b7f` | unclassified |
| `research/59-exact-release-trace-a01-20261005` | `583732554c2ca687fd005e79f5497bb660872bc1` | unclassified |
| `research/59-expected-key-provenance-a01-20261005` | `9ec46a5782257f6e47b6bd4cc28c5bdb1babd58f` | unclassified |
| `research/59-owner-expiry-drain-barrier-a01-20261005` | `70c76483c46108bdd70bf2fb90679d948a5f156f` | unclassified |
| `research/59-owner-hold-retirement-a01-20261005` | `2f98bebc6352a3dd42da37487f7c340c0cf12f50` | unclassified |
| `research/59-per-key-release-receipts-20261005` | `30cdf5f575a64142077c305e110ed5d276c1458c` | unclassified |
| `research/59-release-query-failure-probe-a01-20261005` | `4c429ef3a58f14dd26b1c0e98632bb739de173a6` | unclassified |
| `research/59-renewal-soft-stale-admission-a01-20261005` | `66ba74f69d1373399811f62ad950743caad770ed` | unclassified |
| `research/59-v12-source-closure-20261005` | `9984f00db3b8d4b94c55d64b58f9c4014a760906` | unclassified |
| `research/59-v15-owner-evidence-current-main-20261005` | `8f5beb06d99eed093176c37a74f3620511f984fc` | hold: 20 branch-only commits; unresolved reproduction finding |
| `research/59-v39-audit-chronology-20261005` | `c68aec1407f7dbcf1b3011cade5cbd7063b4bcf1` | unclassified |
| `research/59-v39-cover-admission-main-port-a01` | `a49d08f4def42ca5d8c2e7962b639ba4f277bfcb` | unclassified |
| `research/59-v39-current-admission-fix-a01-20261005` | `1403c822609395f9ab21e0cdbb36b7b4c8ee044d` | unclassified |
| `research/59-v39-fire-cover-ammo-audit-a01-20261005` | `52a51142b10aeb54db3f7b782385d3b941b7429e` | unclassified |
| `research/59-v39-frame-only-threat-a01-20261005` | `8e03ae802e98f70491506082b74e99baa4bbc98c` | unclassified |
| `research/59-v39-keymap-batch-a06-20261005` | `0a43cd9528c1de28af389945c8ce31b3e33e8bf5` | unclassified |
| `research/59-v39-perkey-cleanup-a09-20261005` | `db8585bfc8c9806a0c3dadf7cc95a1d160c81858` | unclassified |
| `research/59-v39-renewal-invalidation-a01-20261005` | `fc3d88686ef17d3d9b721592eb64d862890cff8b` | unclassified |
| `research/59-v39-renewal-reject-race-a01-20261005` | `9234613a2396040eb5352318e50b06a2467d432e` | unclassified |
| `research/59-v39-startup-edge-identity-audit-a01-20261005` | `108d22491db4baf6aa7214ae3f94122f3a7bf849` | unclassified |
| `research/59-v39-v15-cleanup-a05-current-main-20261005` | `4ede220fc567e74d4d7432b6eda3ade7652d8550` | hold: source history pending #8161 integration/review |
| `research/59-v39-v15-cleanup-a07-current-main-20261005` | `fdfcbb03d8bec4bbb532a3f46325fd5ef62205ef` | unclassified |
| `research/59-xvfb-audit-v3-a02-20261005` | `1ec6556ba8568de289625b5f167e7b8c21e1f72c` | hold: run/result custody unresolved |
| `research/7993-superpopulation-ipcw-a02-construction-20261005` | `0a26e2e5802ee26fbb8198184b95856c336c7bda` | unclassified |
| `research/8068-imperfect-repair-t0-a01-20261005` | `c3cdedfe68ef4adb240d5ab5313b8285c9140d9f` | unclassified |
| `research/8150-threat-profiled-runtime-eligibility-t0-20261005` | `e9ad794f0b4b98c5fcb8532777c40c16a9070306` | unclassified |
| `test/59-feedback-before-step-bool-20261005` | `6bde1d9bd634d94f59a20c898ec1c67d737dbcf9` | unclassified |
| `test/59-v39-adapter-edge-cardinality-a01-20261005` | `af2ba4249a9f282f6b7c3fa3e0cca68c077aaa63` | unclassified |
| `test/59-v39-observation-step-alias-20261005` | `bb2b3f4d81b18ec85b13e079e46debd6c3b1b05f` | unclassified |
| `test/7974-single-query-failure-boundary` | `95666c514f142b58cebafc1920b86bcd87a0d8be` | unclassified |

Do not delete any other ref based on this census alone.

## Correction: #7974 follow-up branch disposition — 2026-10-05 12:35 UTC

The earlier note that the #7974 branch was checked out is superseded by a fresh worktree inspection at 12:33 UTC: no local worktree used `fix/59-v15-per-key-keyup-retry-a01-20261005`. Its remote tip was `23aa99031d7e0178de5f69f6df8e89fb63b1d9a6`; its two commits beyond main were the synchronization merge and `a89cbae943838013414e7f70040639e41e0ed816`.

At the same capture, main was `307b9e2f0420f130e9d933c037cac78501d2e547`. Both #7974's merge commit `ec63985e6312e79a2b82e88c4f83369b2d969e0e` and #8067's merge commit `64dcc4c677202eb9b1c9b41ff808e56486c8321f` were ancestors of main. The candidate branch's `git merge-tree --write-tree` result was exactly main's tree `c4912c68edac9133c0bbabd466bdd69ede7b4b42`; the change in `a89cbae` has the same stable patch-id as #8067's merged test change, and that test content is present on main. The candidate branch was not the head or base of any of the 336 open PRs queried, and no worktree used it. Thus its unique commit identity is not in main ancestry, but its complete source diff is represented by #8067 on main.

The remote branch ref was deleted after these checks. To retain the exact former branch history, annotated tag `archive/branch-fix-59-v15-per-key-keyup-retry-a01-20261005` points to the former tip. PR head refs #7974 (`02370aa7ed5bb4a1d0bd483858e6491294bcf139`) and #8067 (`ce1e2e732c5df127037490c2b8dba60675404b68`) remain available. The three closed child-PR branches (#8048, #8012, #7958) were verified present before deletion and were left untouched. No claim is made that those child branches or PRs are integrated.


## Current remote-ref recheck — 2026-10-05 12:44 UTC

The dated 12:25 census above is retained as history. A fresh, paginated but non-atomic read observed main `b5be19963454ce5edafc945b78b100012952dd15`, **406 branch refs**, and **340 open PRs** (312 Draft, 28 Ready). All 340 open PR head refs existed and matched their branch-tip SHAs (340/340). Sixty-five refs were not used as open-PR heads. The snapshot's 65 exact tips are listed below. A count or an unclassified label is not authority to delete a ref.

Since the prior census, the #7974 branch was removed after the recorded content/ancestry/worktree audit; `research/59-v39-perkey-cleanup-a09-20261005` was removed after PR #8196 confirmed all 26 source package blobs were preserved; the #8191 successor branch is now an open-PR head and is excluded from this non-PR set. The new current non-PR set differs from the earlier table, so use this table for the 12:44 UTC snapshot. #8202 was closed as duplicate and its branch removed after all 26 original #8142 blobs were confirmed byte-identical in #8196's proposed A08 STOP and A09 receipt custody package. PR #8196 remains a draft, unmerged rescue proposal pending independent review.

| Ref | Tip SHA | Current disposition |
| --- | --- | --- |
| `codex/fix-7997-evidence-wording` | `819f2c302109d961b8f9578f12e1d81d26b12786` | unclassified |
| `fix/compiled-observation-exception-propagation-20261005` | `68a5f26670f359bd5085dd47ccfcb43ce2c74151` | unclassified |
| `fix/retain-unverified-x11-key-holds-20261005` | `416846ef59b08c862cca84c128d1853e16a6143a` | unclassified |
| `fix/scorer-endpoint-read-type-7685-a01` | `fc8d12f13519811491015f4e2ecdd847246c55d4` | unclassified |
| `fix/x11-explicit-up-01a0ff2c` | `64b143a78f23d3e9acb229300eb195fcaf66851e` | unclassified |
| `fix/x11-wheel-ledger-01a0ff2c` | `ed7bb24e45fac16114e1247e00c8ed86cebda5c8` | unclassified |
| `fix/59-a05-audit-integrity-20261005` | `0dcd3abb9ce99b6a3f596277f124e304ed62a5fc` | unclassified |
| `fix/59-feedback-step-bool-identity-20261005` | `2bebf57d9eb617bb20ef4fbbfa6ad13f1a4ba5f0` | unclassified |
| `fix/59-projector-attempt-ordinal-type-e0cc-20261005` | `6be323b3f3ccb7c94f2bd684864e246eab8e6914` | unclassified |
| `fix/59-scorer-readback-type-20261005` | `614348df05ae603526a6a74a8feec17f039e7927` | unclassified |
| `fix/59-v39-admission-id-projection-a01-20261005` | `191ba71fbfc339cd57e80bcf69dfcc856e6a2feb` | unclassified |
| `fix/59-v39-app-consumption-contradiction-20261005` | `efb712b1aa6f01d67ed119b266ef479645cfb96a` | unclassified |
| `fix/59-v39-app-consumption-sample-depth-a01-20261005` | `826329b2ff0adf0bd963c26c5b4ced2ec3fc69cb` | unclassified |
| `fix/59-v39-bracket-interval-bool-20261005` | `a427bdf9c2e76f8cc905946aa8b08f0ed26597cc` | unclassified |
| `fix/59-v39-cover-admission-invalidation-edd067-20261004` | `763ff69a531eb47a6a3f033f56171dffc80afa23` | unclassified |
| `fix/59-v39-hashsafe-adapter-id-20261005` | `40c056e322b39bbb11cb0d02aec7d8edf66367aa` | unclassified |
| `fix/59-v39-raw-bracket-consistency-a01-20261004` | `971234f7a186960cbd519c655beccbab42854a67` | unclassified |
| `fix/59-v39-typed-state-feedback-20261004` | `8bfe24520490e2bf2c6ef0288edf3e1f3c03a65a` | unclassified |
| `fix/59-wheel-release-ledger-20261005` | `e14c8267854e24e5978767cd53065622abdee3f6` | unclassified |
| `fix/59-windows-anonymous-pipe-readiness-20261005` | `67905decc40a468b9dfe45ecfbcc8a6b83999689` | unclassified |
| `fix/7849-preflight-cleanup-result-20261005` | `979e9a57db800e8f5c63ce0810c3228346e2be3b` | unclassified |
| `fix/7974-release-lockout-a01-20261005` | `5d18a471c9463a660d97e24eed9c2f863ff55bd6` | unclassified |
| `maintenance/inventory-followup-20261005` | `3b1c12ca6ebc01101aad443c71601efbc17c85c0` | unclassified |
| `rescue/constructor-close-fdfd-20261004` | `203cd69ad14aea0a05d5600ee9ace177578b51d5` | unclassified |
| `rescue/todomvc-route-b714-20261004` | `004174810fdb8cb93b95f052ebf1a764f0e64478` | unclassified |
| `rescue/59-per-key-interval-a01-a02-20261005` | `ec44484c35075994d72b25a2ae021a91041da75d` | unclassified |
| `research/scorer-endpoint-readback-type-20261005` | `39bf575ccf0c4795a0a81d06baf08e1a36a2d114` | unclassified |
| `research/strict-attempt-ordinal-v39-20261005` | `4d79f5b97d0c467d7af62046cdfcf1af69754252` | unclassified |
| `research/v15-perkey-owner-evidence-only-20261005` | `0758b536b7b02265c8375ef70bc6703dcee77bc9` | unclassified |
| `research/v39-attempt-ordinal-exact-int-20261005` | `c405b129e83c613e815160f841070ed68267be1d` | unclassified |
| `research/v39-dual-signal-epoch-a03-20261005` | `1665dff09fca6d367e41d469492935604c65f0fd` | unclassified |
| `research/v39-partial-record-drain-race-20261005` | `d76e9945bce4b6ef0b8df79fbabf1b8ee5516815` | unclassified |
| `research/59-audit-readonly-v2-20261005` | `f191772c48fc9dfd8f33760e2b6a243b890b4a38` | unclassified |
| `research/59-cancel-release-cause-postsample-c03-20261004` | `e101c63ac4938ed4017e3021338ebd1c333d8c29` | unclassified |
| `research/59-effect-identity-join-a01-20261005` | `b9dbe5f6f4086b402e3ce23c347d38fe155d5b7f` | unclassified |
| `research/59-exact-release-trace-a01-20261005` | `583732554c2ca687fd005e79f5497bb660872bc1` | unclassified |
| `research/59-expected-key-provenance-a01-20261005` | `9ec46a5782257f6e47b6bd4cc28c5bdb1babd58f` | unclassified |
| `research/59-owner-expiry-drain-barrier-a01-20261005` | `70c76483c46108bdd70bf2fb90679d948a5f156f` | unclassified |
| `research/59-owner-hold-retirement-a01-20261005` | `2f98bebc6352a3dd42da37487f7c340c0cf12f50` | unclassified |
| `research/59-per-key-release-receipts-20261005` | `30cdf5f575a64142077c305e110ed5d276c1458c` | unclassified |
| `research/59-release-query-failure-probe-a01-20261005` | `4c429ef3a58f14dd26b1c0e98632bb739de173a6` | unclassified |
| `research/59-renewal-soft-stale-admission-a01-20261005` | `66ba74f69d1373399811f62ad950743caad770ed` | unclassified |
| `research/59-unauthored-health-trigger-replay-a01-20261005` | `a344436b5aec74d1a1b548bb773983e30c5cb525` | unclassified; current tip not in prior snapshot |
| `research/59-v12-source-closure-20261005` | `9984f00db3b8d4b94c55d64b58f9c4014a760906` | unclassified |
| `research/59-v15-owner-evidence-current-main-20261005` | `8f5beb06d99eed093176c37a74f3620511f984fc` | hold: 20 branch-only commits; unresolved reproduction finding |
| `research/59-v39-audit-chronology-20261005` | `c68aec1407f7dbcf1b3011cade5cbd7063b4bcf1` | unclassified |
| `research/59-v39-cover-admission-main-port-a01` | `a49d08f4def42ca5d8c2e7962b639ba4f277bfcb` | unclassified |
| `research/59-v39-current-admission-fix-a01-20261005` | `1403c822609395f9ab21e0cdbb36b7b4c8ee044d` | unclassified |
| `research/59-v39-fire-cover-ammo-audit-a01-20261005` | `52a51142b10aeb54db3f7b782385d3b941b7429e` | unclassified |
| `research/59-v39-frame-only-threat-a01-20261005` | `8e03ae802e98f70491506082b74e99baa4bbc98c` | unclassified |
| `research/59-v39-keymap-batch-a06-20261005` | `0a43cd9528c1de28af389945c8ce31b3e33e8bf5` | unclassified |
| `research/59-v39-renewal-invalidation-a01-20261005` | `fc3d88686ef17d3d9b721592eb64d862890cff8b` | unclassified |
| `research/59-v39-renewal-reject-race-a01-20261005` | `9234613a2396040eb5352318e50b06a2467d432e` | unclassified |
| `research/59-v39-startup-edge-identity-audit-a01-20261005` | `108d22491db4baf6aa7214ae3f94122f3a7bf849` | unclassified |
| `research/59-v39-v15-cleanup-a05-current-main-20261005` | `4ede220fc567e74d4d7432b6eda3ade7652d8550` | hold: source history pending #8161 integration/review |
| `research/59-v39-v15-cleanup-a07-current-main-20261005` | `fdfcbb03d8bec4bbb532a3f46325fd5ef62205ef` | unclassified |
| `research/59-xvfb-audit-v3-a02-20261005` | `1ec6556ba8568de289625b5f167e7b8c21e1f72c` | hold: run/result custody unresolved |
| `research/7993-superpopulation-ipcw-a02-construction-20261005` | `0a26e2e5802ee26fbb8198184b95856c336c7bda` | unclassified |
| `research/8068-imperfect-repair-t0-a01-20261005` | `c3cdedfe68ef4adb240d5ab5313b8285c9140d9f` | unclassified |
| `research/8150-threat-profiled-runtime-eligibility-t0-20261005` | `e9ad794f0b4b98c5fcb8532777c40c16a9070306` | unclassified |
| `research/8185-transform-graph-a02-20261005` | `c0f8e1b690d86a7ff10cecf47d9bb16fcd79d053` | unclassified; current tip not in prior snapshot |
| `test/59-feedback-before-step-bool-20261005` | `6bde1d9bd634d94f59a20c898ec1c67d737dbcf9` | unclassified |
| `test/59-v39-adapter-edge-cardinality-a01-20261005` | `af2ba4249a9f282f6b7c3fa3e0cca68c077aaa63` | unclassified |
| `test/59-v39-observation-step-alias-20261005` | `bb2b3f4d81b18ec85b13e079e46debd6c3b1b05f` | unclassified |
| `test/7974-single-query-failure-boundary` | `95666c514f142b58cebafc1920b86bcd87a0d8be` | unclassified |

This is another read-only census. Do not infer that all 65 refs are disposable; per-ref content, ancestry, PR dependencies, custody, and worktree ownership still require audit.


## Worktree ownership corrections — 2026-10-05 12:45 UTC

A fresh local `git worktree list --porcelain` after the 12:44 remote-ref census found two clean local checkouts that affect disposition:

- `research/59-v39-v15-cleanup-a07-current-main-20261005` remains checked out at `fdfcbb03d8bec4bbb532a3f46325fd5ef62205ef`. Closed PR #8130's author comment identifies the same A07 pre-treatment focus-admission STOP as the canonical #8126 package and calls #8130 corroborating evidence, but the existing worktree is an active ownership claim. Keep the remote branch until that checkout is retired or its owner reconciles it; do not delete based on the duplicate-science note alone.
- `fix/59-v15-per-key-keyup-retry-a01-20261005` has no remote branch ref after the earlier audited removal, but a clean local worktree is currently on local commit `6edb4ce5107a6f99fce7dc94613e160fe0777ba4`. The earlier removal was based on the 12:33 no-worktree observation; this later checkout does not restore the remote ref automatically. Preserve the local checkout and its history, and do not prune it. The archival tag and closed PR refs cited above remain the remote recovery points.

The current 12:44 table remains a remote-ref snapshot. Worktree ownership is local state and must be checked again before any later branch deletion.


## Additional local worktree holds — 2026-10-05 12:46 UTC

A subsequent read of the shared local repository's worktree registry found three of the 65 remote refs in clean local worktrees at the exact remote tips recorded in the 12:44 table. Keep these remote refs while the checkouts exist; do not delete them as unclassified refs:

- `fix/59-v39-hashsafe-adapter-id-20261005` at `40c056e322b39bbb11cb0d02aec7d8edf66367aa`.
- `fix/59-v39-app-consumption-sample-depth-a01-20261005` at `826329b2ff0adf0bd963c26c5b4ced2ec3fc69cb`.
- `research/59-v39-v15-cleanup-a07-current-main-20261005` at `fdfcbb03d8bec4bbb532a3f46325fd5ef62205ef` (also noted in the preceding correction).

The three observed worktrees had clean status. The two first refs have no open PR head. Their branch owners and closed-PR history still need review before any later disposition. Including the local worktree for the already-removed #7974 ref noted above, four relevant checkouts remain; only three correspond to refs in the current 65-ref remote snapshot. This corrects the shorthand “two now have worktree holds” in the PR description.


## Follow-up transactions — 2026-10-05 12:57 UTC

This is a delta record, not a refresh of the repository-wide CSV census above.

- Local `main` was fast-forwarded from `2c1c90c80389dc6aab6a950c7058528272979f2d` to the already observed `origin/main` tip `b5be19963454ce5edafc945b78b100012952dd15`; the remote `main` ref was not changed.
- Removed three local-only cached PR-head aliases (`origin/pr-8110-head`, `origin/pr-8139-head`, `origin/pr-8146-head`) after confirming each SHA exactly matched its still-existing live PR head branch. No remote branch or PR was deleted. Mismatched historical aliases were retained.
- Consolidated Issue #8088 A02's full evidence directory into the corrected A03 branch for PR #8204. All 18 original Git blobs match the original A02 branch; the 17 SHA256SUMS entries pass. PR #8198 was closed unmerged as superseded, while its remote branch at `af7b4af7072aa519d6ec4845731eab3b309bf80d` remains intact. PR #8204 stays open for review at `1bac5efaa02a1f198ac22347915a0a4e11a6fcf0` on base `b5be19963454ce5edafc945b78b100012952dd15`. No formal allocation was rerun.
- The local `work/pr8096-refresh` checkout is now on the A03 inventory-rescue branch. Its A05 V15 closure commit remains on branch `research/59-v15-release-closure-a03-20261005` and remote PR #8096; no evidence branch was deleted.


## Current remote-ref recheck — 2026-10-05 12:59 UTC

A new paginated, non-atomic census after the 12:44 snapshot observed main `b5be19963454ce5edafc945b78b100012952dd15`, **406 branch refs**, and **344 open PRs** (315 Draft, 29 Ready). All 344 open PR heads existed and matched the branch-tip SHA (344/344). Sixty-one other refs were not open-PR heads. Exact current tips and dispositions are listed here; earlier tables remain historical snapshots.

Since 12:44 UTC, `fix/7849-preflight-cleanup-result-20261005` was removed from remote after a closed-PR/successor/worktree audit. Its closed PR #7859 head remains available, and the A01 result blob matches the exact result on the active #7849 branch. Other remote refs changed while this non-atomic census was being collected; use only the current list below for this snapshot. #8198's former branch is now held as evidence provenance for successor #8204. Current local worktree checks hold two of these 61 remote refs; the removed #7974 remote branch still has a separate clean local checkout as recorded above.

| Ref | Tip SHA | Current disposition |
| --- | --- | --- |
| `codex/fix-7997-evidence-wording` | `819f2c302109d961b8f9578f12e1d81d26b12786` | unclassified |
| `fix/compiled-observation-exception-propagation-20261005` | `68a5f26670f359bd5085dd47ccfcb43ce2c74151` | unclassified |
| `fix/retain-unverified-x11-key-holds-20261005` | `416846ef59b08c862cca84c128d1853e16a6143a` | unclassified |
| `fix/scorer-endpoint-read-type-7685-a01` | `fc8d12f13519811491015f4e2ecdd847246c55d4` | unclassified |
| `fix/x11-explicit-up-01a0ff2c` | `64b143a78f23d3e9acb229300eb195fcaf66851e` | unclassified |
| `fix/x11-wheel-ledger-01a0ff2c` | `ed7bb24e45fac16114e1247e00c8ed86cebda5c8` | unclassified |
| `fix/59-a05-audit-integrity-20261005` | `0dcd3abb9ce99b6a3f596277f124e304ed62a5fc` | unclassified |
| `fix/59-feedback-step-bool-identity-20261005` | `2bebf57d9eb617bb20ef4fbbfa6ad13f1a4ba5f0` | unclassified |
| `fix/59-projector-attempt-ordinal-type-e0cc-20261005` | `6be323b3f3ccb7c94f2bd684864e246eab8e6914` | unclassified |
| `fix/59-scorer-readback-type-20261005` | `614348df05ae603526a6a74a8feec17f039e7927` | unclassified |
| `fix/59-v39-admission-id-projection-a01-20261005` | `191ba71fbfc339cd57e80bcf69dfcc856e6a2feb` | unclassified |
| `fix/59-v39-app-consumption-contradiction-20261005` | `efb712b1aa6f01d67ed119b266ef479645cfb96a` | unclassified |
| `fix/59-v39-bracket-interval-bool-20261005` | `a427bdf9c2e76f8cc905946aa8b08f0ed26597cc` | unclassified |
| `fix/59-v39-cover-admission-invalidation-edd067-20261004` | `763ff69a531eb47a6a3f033f56171dffc80afa23` | unclassified |
| `fix/59-v39-hashsafe-adapter-id-20261005` | `40c056e322b39bbb11cb0d02aec7d8edf66367aa` | hold: clean local worktree at this exact tip; no deletion |
| `fix/59-v39-raw-bracket-consistency-a01-20261004` | `971234f7a186960cbd519c655beccbab42854a67` | unclassified |
| `fix/59-v39-typed-state-feedback-20261004` | `8bfe24520490e2bf2c6ef0288edf3e1f3c03a65a` | unclassified |
| `fix/59-wheel-release-ledger-20261005` | `e14c8267854e24e5978767cd53065622abdee3f6` | unclassified |
| `fix/59-windows-anonymous-pipe-readiness-20261005` | `67905decc40a468b9dfe45ecfbcc8a6b83999689` | unclassified |
| `fix/7974-release-lockout-a01-20261005` | `5d18a471c9463a660d97e24eed9c2f863ff55bd6` | unclassified |
| `maintenance/inventory-followup-20261005` | `3b1c12ca6ebc01101aad443c71601efbc17c85c0` | unclassified |
| `rescue/constructor-close-fdfd-20261004` | `203cd69ad14aea0a05d5600ee9ace177578b51d5` | unclassified |
| `rescue/todomvc-route-b714-20261004` | `004174810fdb8cb93b95f052ebf1a764f0e64478` | unclassified |
| `rescue/59-per-key-interval-a01-a02-20261005` | `ec44484c35075994d72b25a2ae021a91041da75d` | unclassified |
| `research/scorer-endpoint-readback-type-20261005` | `39bf575ccf0c4795a0a81d06baf08e1a36a2d114` | unclassified |
| `research/spec-diversity-8088-t0-a02-20261005` | `af7b4af7072aa519d6ec4845731eab3b309bf80d` | hold: #8198 closed unmerged; evidence copied with blob identity to successor PR #8204; source branch retained |
| `research/strict-attempt-ordinal-v39-20261005` | `4d79f5b97d0c467d7af62046cdfcf1af69754252` | unclassified |
| `research/v15-perkey-owner-evidence-only-20261005` | `0758b536b7b02265c8375ef70bc6703dcee77bc9` | unclassified |
| `research/v39-attempt-ordinal-exact-int-20261005` | `c405b129e83c613e815160f841070ed68267be1d` | unclassified |
| `research/v39-dual-signal-epoch-a03-20261005` | `1665dff09fca6d367e41d469492935604c65f0fd` | unclassified |
| `research/v39-partial-record-drain-race-20261005` | `d76e9945bce4b6ef0b8df79fbabf1b8ee5516815` | unclassified |
| `research/59-cancel-release-cause-postsample-c03-20261004` | `e101c63ac4938ed4017e3021338ebd1c333d8c29` | unclassified |
| `research/59-effect-identity-join-a01-20261005` | `b9dbe5f6f4086b402e3ce23c347d38fe155d5b7f` | unclassified |
| `research/59-exact-release-trace-a01-20261005` | `583732554c2ca687fd005e79f5497bb660872bc1` | unclassified |
| `research/59-expected-key-provenance-a01-20261005` | `9ec46a5782257f6e47b6bd4cc28c5bdb1babd58f` | unclassified |
| `research/59-owner-expiry-drain-barrier-a01-20261005` | `70c76483c46108bdd70bf2fb90679d948a5f156f` | unclassified |
| `research/59-owner-hold-retirement-a01-20261005` | `2f98bebc6352a3dd42da37487f7c340c0cf12f50` | unclassified |
| `research/59-per-key-release-receipts-20261005` | `30cdf5f575a64142077c305e110ed5d276c1458c` | unclassified |
| `research/59-release-query-failure-probe-a01-20261005` | `4c429ef3a58f14dd26b1c0e98632bb739de173a6` | unclassified |
| `research/59-renewal-soft-stale-admission-a01-20261005` | `66ba74f69d1373399811f62ad950743caad770ed` | unclassified |
| `research/59-v12-source-closure-20261005` | `9984f00db3b8d4b94c55d64b58f9c4014a760906` | unclassified |
| `research/59-v15-owner-evidence-current-main-20261005` | `8f5beb06d99eed093176c37a74f3620511f984fc` | hold: 20 branch-only commits; unresolved reproduction finding |
| `research/59-v39-cover-admission-main-port-a01` | `a49d08f4def42ca5d8c2e7962b639ba4f277bfcb` | unclassified |
| `research/59-v39-current-admission-fix-a01-20261005` | `1403c822609395f9ab21e0cdbb36b7b4c8ee044d` | unclassified |
| `research/59-v39-fire-cover-ammo-audit-a01-20261005` | `52a51142b10aeb54db3f7b782385d3b941b7429e` | unclassified |
| `research/59-v39-frame-only-threat-a01-20261005` | `8e03ae802e98f70491506082b74e99baa4bbc98c` | unclassified |
| `research/59-v39-keymap-batch-a06-20261005` | `0a43cd9528c1de28af389945c8ce31b3e33e8bf5` | unclassified |
| `research/59-v39-renewal-invalidation-a01-20261005` | `fc3d88686ef17d3d9b721592eb64d862890cff8b` | unclassified |
| `research/59-v39-renewal-reject-race-a01-20261005` | `9234613a2396040eb5352318e50b06a2467d432e` | unclassified |
| `research/59-v39-startup-edge-identity-audit-a01-20261005` | `108d22491db4baf6aa7214ae3f94122f3a7bf849` | unclassified |
| `research/59-v39-v15-cleanup-a05-current-main-20261005` | `4ede220fc567e74d4d7432b6eda3ade7652d8550` | hold: source history pending #8161 integration/review |
| `research/59-v39-v15-cleanup-a07-current-main-20261005` | `fdfcbb03d8bec4bbb532a3f46325fd5ef62205ef` | hold: clean local worktree at this exact tip; closed #8130 calls it corroborating A07 STOP |
| `research/59-xvfb-audit-v3-a02-20261005` | `1ec6556ba8568de289625b5f167e7b8c21e1f72c` | hold: run/result custody unresolved |
| `research/7993-superpopulation-ipcw-a02-construction-20261005` | `0a26e2e5802ee26fbb8198184b95856c336c7bda` | unclassified |
| `research/8068-imperfect-repair-t0-a01-20261005` | `c3cdedfe68ef4adb240d5ab5313b8285c9140d9f` | unclassified |
| `research/8150-threat-profiled-runtime-eligibility-t0-20261005` | `e9ad794f0b4b98c5fcb8532777c40c16a9070306` | unclassified |
| `research/8185-transform-graph-a02-20261005` | `c0f8e1b690d86a7ff10cecf47d9bb16fcd79d053` | unclassified; current tip not in prior snapshot |
| `test/59-feedback-before-step-bool-20261005` | `6bde1d9bd634d94f59a20c898ec1c67d737dbcf9` | unclassified |
| `test/59-v39-adapter-edge-cardinality-a01-20261005` | `af2ba4249a9f282f6b7c3fa3e0cca68c077aaa63` | unclassified |
| `test/59-v39-observation-step-alias-20261005` | `bb2b3f4d81b18ec85b13e079e46debd6c3b1b05f` | unclassified |
| `test/7974-single-query-failure-boundary` | `95666c514f142b58cebafc1920b86bcd87a0d8be` | unclassified |

The snapshot is not deletion authority. Refresh each ref's PR use, commit/content custody, dependencies, and local worktree status immediately before acting.


## Follow-up custody decision — X11 cleanup source branch — 2026-10-05 13:15 UTC

Keep remote branch `fix/retain-unverified-x11-key-holds-20261005` at `416846ef59b08c862cca84c128d1853e16a6143a`. Closed PR [#7910](https://github.com/Unjuno/agent-interface/pull/7910) is explicitly superseded and unmerged. Its author's final mapping comment says the implementation and button recovery/no-duplicate behavior are carried by #7974, key recovery tests by #8012, and explicitly says the remote branch remains intact for provenance and recovery. The branch still has three commits beyond merge base `018934cdf45fcabffcc4efe25b5c7b3d59bd459f` and differs in `research/live_control/input_owner_v12.py` plus its cleanup regression; it is not fully represented by current main. A current local worktree search found no checkout on this branch. The explicit provenance hold governs, so no branch deletion or rewrite is made. This supplements the 12:59 census row marked unclassified; it does not change the historical census.


## Follow-up custody decision — Issue #8185 A02 design branch — 2026-10-05 13:16 UTC

Retain `research/8185-transform-graph-a02-20261005` at `c0f8e1b690d86a7ff10cecf47d9bb16fcd79d053` pending an explicit lineage/disposition decision. Its only branch-only path against current main `b5be19963454ce5edafc945b78b100012952dd15` is `research/analysis/epoch_transform_chain_8185_a02_20261005/DESIGN.md`; the document identifies itself as an unfrozen design with no allocation authorized. No worktree uses this branch. The active related PRs #8205 (pre-candidate OrbStack STOP) and #8211 (separate fair exact-oracle A02 result) do not list `DESIGN.md` among their changed files, so its bytes are not yet on main or those successor heads. Preserve this design provenance until its owner reconciles it with the successor record; do not represent it as an experiment result or delete its only ref. This supplements the 12:59 census row marked unclassified.

## Closed-parent stack blockers — 2026-10-05 13:21 UTC

A fresh open-PR snapshot (345 open PRs) found 45 PRs targeting 34 non-main branches. Thirty-seven target another currently open PR head. Eight open PRs instead target three parent branches whose parent PRs are closed-unmerged; those bases are still referenced by open children, so they are not orphan refs and must not be deleted or retargeted mechanically:

- Closed-unmerged #7602 (`fix/59-v39-typed-state-feedback-20261004`, current ref `8bfe24520490e2bf2c6ef0288edf3e1f3c03a65a`) remains the base of #7751, #7696, #7690, #7637, and #7624. Their recorded base SHAs differ (`4c012333`, `a7f9e9e3`, and `40c6a278`). At main `b5be19963454ce5edafc945b78b100012952dd15`, the parent branch diverged by 305 main-only and 47 branch-only commits. Review its unique source/evidence and owner disposition before changing this stack.
- Closed-unmerged #7662 (`fix/59-v39-app-consumption-contradiction-20261005`, ref `efb712b1aa6f01d67ed119b266ef479645cfb96a`) is the base of open draft #7677 (base SHA `d302d8ab6261892b628a8489b9857d3b92a0d237`). Its evidence PR body says the A01 comparison is distinct from the later source fix; preserve it pending a path-level successor audit.
- Closed-unmerged #7847 (`research/59-owner-hold-retirement-a01-20261005`, ref `2f98bebc6352a3dd42da37487f7c340c0cf12f50`) remains the base of open drafts #7864 and #7858 (both base SHA `84985b2b878f99551ab924fbc1351139915f5cc0`). Preserve the parent lineage and both child packages until their owner and evidence dependencies are resolved.

This is a dependency map and hold, not a recommendation to merge or close these PRs. The parent/child base SHAs are not interchangeable, and the all-ref owner and unique-commit audit remains incomplete.


## Current remote-ref recheck and cleanup transaction — 2026-10-05 13:32 UTC

Fresh paginated, non-atomic reads after the branch-custody operation observed main `b5be19963454ce5edafc945b78b100012952dd15`, **407 branch refs**, and **346 open PRs** (316 Draft, 30 Ready). Every open PR head had a matching branch ref and identical SHA (346/346). Sixty refs had no matching open-PR head. Compared with the 13:21 snapshot, the sole ref change was removal of `rescue/todomvc-route-b714-20261004` at `004174810fdb8cb93b95f052ebf1a764f0e64478`; all other orphan names and tips were unchanged. The shared local registry still has two worktrees on orphan refs: `fix/59-v39-hashsafe-adapter-id-20261005` at `40c056e322b39bbb11cb0d02aec7d8edf66367aa` and `research/59-v39-v15-cleanup-a07-current-main-20261005` at `fdfcbb03d8bec4bbb532a3f46325fd5ef62205ef`. Three current orphan refs are bases of open dependent PRs: `fix/59-v39-app-consumption-contradiction-20261005` (#7677), `fix/59-v39-typed-state-feedback-20261004` (#7751, #7696, #7690, #7637, #7624), and `research/59-owner-hold-retirement-a01-20261005` (#7864, #7858). Those refs remain held. Counts remain census context, not deletion grounds.

**Deleted source ref after per-ref custody audit:** `rescue/todomvc-route-b714-20261004` was deleted with an exact expected-tip lease. Closed PR #7297 said its source branch was retained pending separate branch-custody cleanup; its complete 53-file packet and two rescue qualification files were preserved by blob identity in the current-main successor PR #8164. Local Git tree comparison confirmed all 55 packet/qualification blobs identical. The inventory index blob has later additive content on #8164, and its TodoMVC source-route entry is present there. Before deletion, there was no open PR using the source branch as head or base and no local worktree on it. After deletion, branch search returned no branch; `refs/pull/7297/head` remained fetchable at the original SHA. #8164 remains open Draft, so this records evidence rescue on a reviewable successor, not integration into main.

**Retain history branch:** `codex/fix-7997-evidence-wording` at `819f2c302109d961b8f9578f12e1d81d26b12786` remains present. Closed PR #8101 was superseded by merged #8106, but its body explicitly says its branch is retained for history. Its README and A04 scope correction are text-identical to current main after CRLF normalization; current main's checksum manifest matches the current-main bytes. Preserve the source ref under that explicit history disposition.


## Current remote-ref recheck and scorer-branch cleanup — 2026-10-05 13:39:43 UTC

Post-cleanup paginated non-atomic reads observed main `b5be19963454ce5edafc945b78b100012952dd15`, **406 branch refs**, and **346 open PRs** (316 Draft, 30 Ready). All open PR heads matched existing branch refs and exact SHAs (346/346); **59 refs** were not open-PR heads. The two orphan worktree holds and three orphan base-dependency branches (eight open dependents total) remain as recorded in the preceding census. No other orphan name or tip changed in this recheck.

**Deleted** `fix/scorer-endpoint-read-type-7685-a01` at exact tip `fc8d12f13519811491015f4e2ecdd847246c55d4`. Closed PR #7691's single source-file blob matched current main exactly; its only other changed path was a test file. Current main already includes the same float (`11.0`) and Boolean (`True`) readback cases with assertions that withhold values from both the row and receipt. The duplicate branch held no result artifacts beyond those source/test paths. Its parent PR #7685 is merged. Fresh open head/base queries and the local worktree registry had no use of the source branch. After deletion, branch search returned no branch while `refs/pull/7691/head` remains fetchable at the original tip. This removal preserves the corrected behavior and regression coverage on main, with the closed PR ref retaining the superseded source history.

## Follow-up: superseded #7974 child refs reclaimed (2026-10-05)

At current `main` `b5be19963454ce5edafc945b78b100012952dd15`, deleted these two unprotected remote refs by exact-tip lease after a fresh audit:

- `test/7974-single-query-failure-boundary` at `95666c514f142b58cebafc1920b86bcd87a0d8be` (closed unmerged PR #8012).
- `fix/59-wheel-release-ledger-20261005` at `e14c8267854e24e5978767cd53065622abdee3f6` (closed unmerged PR #7958).

Neither ref was the head or base of an open PR, and no local worktree used either branch. PR #7974 is merged; its current implementation supersedes the older source deltas. The 36-file `cleanup-carrier-review-e0cc-20261005` and 23-file `wheel-successor-regression-e0cc-20261005` directories are present on main with blob SHAs identical to #7958's head. The #8012 carrier test is preserved byte-for-byte as `carrier-test-original.py.txt`; #7958's strengthened test is preserved byte-for-byte as `strengthened-test.py.txt`. Both closed PR head refs remain fetchable at their former tips after remote branch deletion. No PR state or source evidence was changed; the historical census rows above remain unchanged.

## Follow-up: duplicate #8068 A01 source-ref cleanup (2026-10-05)

Deleted `research/8068-imperfect-repair-t0-a01-20261005` at exact tip `c3cdedfe68ef4adb240d5ab5313b8285c9140d9f` by lease after confirming closed-unmerged PR #8092's correction classifies its separate 12-cell/WSLc-STOP package as a redundant, noncanonical allocation. No open PR used the branch as head or base, and no local worktree used it.

The ten original package files (including raw, WSLc STOP, auditor, and original SHA256SUMS) have blob-identical copies in reviewable Draft PR #8187 at head `45d39341771504492c2baf56f368413fe383e32a`, alongside an archival qualification. The package remains explicitly noncanonical and must not be treated as a successor scientific result. After deletion, PR #8092 still reports the exact former head and its pull-head ref remains fetchable; PR #8187 remains open. This records rescue to a reviewable PR, not integration to main; no allocation was rerun.

## Closed-parent evidence rescue PR status — 2026-10-05 14:07 UTC

- PR [#8213](https://github.com/Unjuno/agent-interface/pull/8213) is open Draft at `0dc222499722e706a4838ab5d2677c02cb8930d2`, based on main `b5be19963454ce5edafc945b78b100012952dd15`. It preserves the feedback-onset custody audit package from the #7602 source line; five open children still target that parent branch. The trace remains on main and key event/report hashes match its manifest.
- PR [#8215](https://github.com/Unjuno/agent-interface/pull/8215) is open Draft at `79d608fbb84fafa5a4bea9d0a20f4fb3a67ade8d`, based on the same main tip. It preserves the distinct 26-file application-consumption A01 package from #7662; open draft #7677 still targets the original source branch. All 25 saved manifest entries and all 26 package blobs were checked.
- At this refresh both heads are mergeable, one commit ahead and zero behind. Submitted-review lists and combined status endpoints return zero records for both. Keep the rescue refs; neither package is integrated into main, and no saved auditor or experiment was rerun.


## Custody clarification — 2026-10-05 14:12 UTC

The earlier 12:59 UTC table marked `research/8150-threat-profiled-runtime-eligibility-t0-20261005` unclassified. A fresh audit at this time found:

- Source ref tip is still `e9ad794f0b4b98c5fcb8532777c40c16a9070306`. PR #8167 is merged; its current-main publication branch carried the six source-branch paths. Each of those six final file blobs matches `main` exactly.
- Comparing `main` to the source ref reports six source-only commits and exactly those six changed paths. No open PR uses the source ref as head or base, and the shared local checkout registry has no worktree on that branch.
- Keep the source ref for now: the six-commit preregistration/freeze history itself is not represented by the merged publication branch's final blobs. The evidence files are rescued to `main`; intermediate source history remains a provenance hold pending a separate history-preservation decision. Do not classify this as disposable merely because its final files match.

This is a per-ref custody decision, not a complete audit of the remaining unclassified refs. No experiment was rerun.


## Superseded branch cleanup — 2026-10-05 14:16 UTC

Removed `fix/59-feedback-step-bool-identity-20261005` at its audited tip `2bebf57d9eb617bb20ef4fbbfa6ad13f1a4ba5f0`.

- Closed unmerged PR #7699 identifies the implementation as duplicated by #7696 and its unique before-frame Boolean alias regression as carried into #7704, then into #7696's current head.
- #7696's open Draft head `c56a07db5f680f1e6d6e130aa94b68bae38645fa` is four commits ahead of the removed tip; its changed files include the V39 controller and typed-feedback test. No open PR used the removed ref as head or base. The current shared worktree registry had no checkout on this branch.
- After deletion, the branch API returned NOT_FOUND. Closed PR #7699 still reports the original head SHA, and the original typed-feedback test blob remains readable at that SHA. No evidence or commit object was rewritten.

This removes one redundant branch ref while retaining its source through descendant #7696 and closed PR history. #7696 remains unmerged and Draft; this deletion does not integrate or approve its changes.


## Rescued evidence branch cleanup — 2026-10-05 14:18 UTC

Removed `research/59-v39-startup-edge-identity-audit-a01-20261005` at audited tip `108d22491db4baf6aa7214ae3f94122f3a7bf849`.

- Its closed, unmerged PR #7901 had been explicitly kept while the 12-file package was absent from `main`. That package was later copied unchanged to PR #7988 and #7988 has merged.
- Rechecked all 12 paths from PR #7901: every Git blob SHA matches current `main`. Comparing `main` to the source tip showed exactly two source-only commits and those 12 package paths; no unrelated source changes.
- No open PR uses the source branch as head or base, and the shared local worktree registry had no checkout on it. The closed PR still records its original head SHA; the original audit result is readable at that commit after deletion.
- The branch endpoint now returns NOT_FOUND. The earlier provenance hold is resolved for the packaged evidence: all 12 files are on `main`, and PR/commit history remains available.

This removes one source ref only; #7901 remains closed unmerged, #7988 remains the merged preservation record, and no experiment was rerun.


## Ref disappearance observed — 2026-10-05 14:20 UTC

A later recheck found `research/59-v39-startup-edge-identity-audit-a01-20261005` absent from both `git ls-remote` and the GitHub branch API (NOT_FOUND). My exact-tip conditional deletion attempt was rejected as stale information, so this record does not attribute the removal to that command. Closed PR #7901 still records head `108d22491db4baf6aa7214ae3f94122f3a7bf849`; the #7901 result blob is still readable at the same SHA on `main`. PR #7988, which carried all 12 matching package blobs, is merged. The disappearance therefore does not lose the rescued package or closed-PR evidence.


## Rescued evidence branch cleanup — 2026-10-05 14:22 UTC

Removed `research/59-effect-identity-join-a01-20261005` at exact audited tip `b9dbe5f6f4086b402e3ce23c347d38fe155d5b7f`.

- The closed PR #7903 had explicitly retained its evidence on the source branch while it was absent from `main`. PR #7988 later rescued the 19-file package unchanged and is now merged.
- Rechecked all 19 #7903 paths: every Git blob SHA matches current `main`. The source ref was one commit ahead of `main`, containing exactly those 19 paths and no unrelated files.
- No open PR used the source ref as head or base; the current shared worktree registry had no checkout on it. The branch API now returns NOT_FOUND. Closed PR #7903 still records its head SHA, and the original result blob remains readable both at that commit and on `main`.
- This resolves the earlier provenance hold for the evidence files. The scoped PASS / HOLD_MISSING_TASK_EFFECT boundary remains preserved; no experiment or auditor was rerun.

This removes one source ref; #7903 remains closed unmerged and #7988 is the merged evidence-preservation record.
