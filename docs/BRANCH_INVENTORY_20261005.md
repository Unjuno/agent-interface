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
