# Repository cleanup inventory — 2026-10-07 12:11 UTC

## Snapshot

Read-only GitHub REST API inventory, cross-checked against fetched Git refs. Main was 9fb2dd6782d1d1477a00d14be870487fd4c54fa2.

- 380 open pull requests: 335 Draft, 45 ready for review; 329 target main, and 51 are stacked on another branch. None was older than 30 days at capture time.
- 450 remote branches.
- The 380 open PR head branches match 380 distinct remote branch tips exactly; zero head-SHA mismatches and zero duplicate-tip groups.
- 70 branch tips have no open PR head. Of these, 2 are ancestors of main (main and research/4435-complete-custody-20261007-k9r2); 68 remain outside main. Three of those 68 are direct bases of open PRs (#7677, #7751/#7696/#7690/#7637/#7624, and #7864/#7858); preserve them as active stack dependencies. The other 65 have no direct open-PR base reference in this snapshot, but still need ancestry, closed-PR, worktree, and evidence-custody checks before any deletion. One unpaired branch is worktree-owned (main).
- Compared with the 2026-10-07 11:54 UTC inventory: open PRs rose from 376 to 380. The branch list grew from 447 at the prior snapshot to 450 in this API capture while a previously seen review ref was removed. Git refs and paginated API results are live data and can change during capture.

## Recent PR and branch changes

- #8296 (fix/8252-held-modifier-current-main) was closed by the repository owner at 12:05 UTC and is unmerged; its branch remains. GitHub reports one bot COMMENTED review and ten successful checks. The review is generic automated-review boilerplate; no disposition explaining closure is visible. Preserve the patch for review/recovery; do not count it as integrated.
- #8298 (fix/57-appserver-write-admission-e0cc-20261007) is open Draft with no reviews. Only the construction check has run and was skipped; it contains implementation changes and retained evidence.
- #8299 (research/5309-precapture-control-a13-20261007) is an additional open PR in the latest snapshot, retaining an A13 pre-freeze execution STOP. Keep this STOP as process evidence; it is not a scientific result.
- #8297 (research/reversibility-7949-external-write-a01-20261007) is open Draft with no reviews. The branch preserves A04 HOLD and A05 scoped PASS alongside earlier STOP artifacts; keep these outcomes distinct.
- #8295 (research/5309-evidence-semantics-a12-20261007) is open and ready, with no reviews; its seven check runs succeeded. The A12 run manifest was separately checked against all 16 listed blobs with zero mismatches. This is a static custody check, not a rerun.
- #8294 remains open and ready, with no reviews. Its replay gate succeeded; formal and construction checks were skipped.
- A09 advanced to f4e7a21bbda3f78286f62674ca7ad7bee9765713; its open-PR crosswalk head matches the GitHub branch tip.



## Follow-up disposition

- After the 12:11 UTC inventory, current main advanced to dd37f2ddbdb0a424e43676545595f5537e435473. Verified the recorded 4435 custody tip is contained in that main, has no PR/worktree/base dependency, and is unprotected; deleted only that remote branch. Its tip remains reachable from main. The deletion is recorded in [branch retirements](BRANCH_RETIREMENTS_20261007_1221Z.csv).

- PR #8295 (A12) merged at 12:17 UTC and PR #8289 (A09) merged at 12:24 UTC. Both source branches are now deleted after verifying exact head-tip reachability from main, zero open PR base dependencies, no worktree owner, and prior API protection=false. PRs #8291/#8292 now target main, so the remaining A10/A11 branches stay under active PRs.

## Live state check — 2026-10-07 12:27 UTC

- Current main is 074f00a0db5baf48a42ed446043f7e1081a40ed7. The retired 4435 custody, A09, and A12 tips remain ancestors of this main.
- GitHub pull dashboard reports 379 open PRs across 16 pages; the list changed during capture, so no fresh PR/branch crosswalk is asserted from that page view.
- [Current branch tips](BRANCH_TIPS_20261007_123127Z.csv) records 447 remote branches at the later 12:53 UTC capture.

- Current PR activity capture: 379 open (335 Draft, 44 ready), 86 updated within 24 hours, 110 within 48 hours, and 130 created over 3 days earlier. This is not an abandonment test; STOP/HOLD evidence and stacked PR dependencies need preservation review. See [activity summary](OPEN_PR_ACTIVITY_20261007_123440Z.md) and [all 379 PR rows](OPEN_PR_ACTIVITY_20261007_123440Z.csv).

- The author deleted fix/x11-explicit-up-01a0ff2c on Oct 7 at 12:34 UTC. Its PR #7114 is closed unmerged and explicitly titled Superseded; the remaining branch delta is three test-file edits and is not integrated. Do not restore or adopt that V2 change. The historical evidence archive was separately rescued by merged PR #7980 (commit 5d896208724f824b7a0490a512bc72340a80bf0d), whose tip is reachable from main and whose MANIFEST.json is present there.

- PR #7148 is closed unmerged but its fix/x11-wheel-ledger-01a0ff2c branch remains outside main. Its last review note says V4 content review SUSPENDED / adoption/application HOLD and explicitly says not to approve, adopt, or apply this head. The four-commit branch changes nine paths relative to its merge base. Preserve it as a held source record; do not delete or merge until a qualified successor resolves the hold.

- PR #8296 was closed unmerged, but its two-commit held-modifier fix passed its original ten checks. Rebased by cherry-picking both commits onto current main in rescue/8252-held-modifier-currentmain-20261007; 59 focused/regression tests and compileall pass. The branch is pushed; a new PR has not been created. See [rescue record](BRANCH_RESCUES_20261007.csv) and compare link.

## Follow-up policy

1. Triage the 65 unpaired, non-main-ancestor branches individually. First identify merged/closed PRs, ancestry and stack dependencies, worktree ownership, evidence custody, and whether each unique change is already integrated. Delete only verified aliases or fully integrated disposable refs; rescue useful evidence to a current-main PR before removing its source ref.
2. Review the 335 Draft PRs for active stacks, explicit STOP/HOLD allocations, and duplicated or superseded work. Preserve each live stack's base/head relationship.
3. Prioritize ready PRs with passing checks for maintainer review. Do not merge on inventory evidence alone.
4. Re-run the complete inventory after these dispositions; this snapshot does not claim the repository is clean or that all 65 unpaired branches are abandoned.

## Snapshot files

- [Latest branch tips](BRANCH_TIPS_20261007_125325Z.csv)
- [Rescued branch record](BRANCH_RESCUES_20261007.csv)

- [Open PRs](OPEN_PRS_20261007_121116Z.csv)
- [Branch tips](BRANCH_TIPS_20261007_121116Z.csv)
- [Branch-to-open-PR crosswalk](BRANCH_CROSSWALK_20261007_121116Z.csv)
- [Unpaired-branch triage](BRANCH_ORPHAN_TRIAGE_20261007_121116Z.csv)
- PR #8308 was opened as a Draft from the rebased rescue branch; it targets current main 798ac5ad709168ff1d27b115f10f4f96b126bb71 and preserves the original source PR #8296 as provenance. Local focused/regression verification is recorded in the rescue ledger; independent review and integration remain pending.

- PR #8308 was refreshed against current main `798ac5ad709168ff1d27b115f10f4f96b126bb71`; new head `2d0f29539904ba053dda49b48666ec220b7ae82e`. The 32+27 targeted local tests, compileall and diff check pass. All 10 current-head GitHub checks now pass. Source-branch deletion is deferred until successor integration to preserve exact commit reachability.
- PR #8292's A11 branch `research/5309-topology-dependent-a11-20261007` was retired after confirming merged PR #8292, exact head `393bfec35cf60e3c57f4438f3bd02a0955b676f4` is an ancestor of current main `8c8b37424fdb43482412240868574813fae46c2e`, no open PR head/base dependents, and no worktree owner. Deletion used an expected-tip lease. The A11 formal FAIL and V3 STOP artifacts remain in main; retirement is recorded in `BRANCH_RETIREMENTS_20261007_1221Z.csv`.
- PR #8291's A10 branch `research/5309-witness-topology-a10-20261007` was retired after verifying merged PR #8291, exact head `e6b6c871a66cb10c026d6119a9033f19bc5fc0d7` is in current main, no open PR head/base dependencies, and no worktree owner. The expected-tip lease deletion succeeded. The A10 formal FAIL remains preserved in main and the retirement is recorded in the branch-retirement ledger.
- Current V15 rescue chain (13:19Z): original closed-unmerged PRs #8079 and #8091 have no matching remote source branch refs, while their evidence is preserved by open Draft #8311 (head `231bdae5dd8e7e0f23ca0e9bd30e7d1129868d2b`, based on main `8c8b37424fdb43482412240868574813fae46c2e`) and stacked Draft #8312 (head `76da0f6aaea6500f40826749fdd064d86caf459c`, based on #8311). #8311 has successful index/replay checks; formal and construction checks are skipped. #8312 retains a separate 22/22 readback and initial missing-Pillow STOP. Keep both Drafts and their dependency until independent review and integration; do not duplicate or promote their construction evidence to live input claims.
- PR #7453's C03 evidence has already been preserved in main by merged PR #8115; its rescue branch is absent. No additional rescue is needed.
- PR #8255 is now merged, although an earlier read returned its pre-merge body. Its exact head `266f07807633807c372e96f850d045241237d033` is an ancestor of main `349dd5f80beaa870dcc97133237cc48c1e979d23` at retirement; current main is `798ac5ad709168ff1d27b115f10f4f96b126bb71`; no open PR head/base dependency or worktree owner remains. The branch was deleted with an expected-tip lease. The research evidence remains in main; retirement is recorded in `BRANCH_RETIREMENTS_20261007_1221Z.csv`.
- At 13:25Z, `git ls-remote --heads` reported 446 branch refs. After fetching current heads, no remote branch tip other than `main` was fully contained in main; remaining branch retirement requires verifying each associated PR and evidence disposition.
## 2026-10-07 branch retirement follow-up (13:47Z)

- Retired remote heads for merged PRs #8315, #8310, and #8306. In each case the exact branch tip matched the merged PR head; the PR merge was integrated into current main `798ac5ad709168ff1d27b115f10f4f96b126bb71`; branch protection was false; an audit of all 381 open PRs found no head or base dependency; and `git worktree list` showed no worktree owner. Each deletion used an expected-tip lease. The corresponding experiment records remain in main through the merged PRs.
- `git ls-remote --heads origin` now reports 446 refs. Retirement rows are in `BRANCH_RETIREMENTS_20261007_1221Z.csv`.
## 2026-10-07 stale-PR follow-up (13:58Z)

- GitHub REST inventory returned 382 open PRs: 334 target `main`, and 325 of those record a base SHA older than current main `798ac5ad709168ff1d27b115f10f4f96b126bb71`. Another 48 are intentionally stacked. Refresh only after checking dependency order and the evidence's frozen inputs; this is not a bulk-rebase instruction.
- PR #8305 was rebased onto current main and its local 5/5 package tests, 769-directory analysis index check, compilation, and diff check pass. Current-head analysis/workspace-index, replay, navigation, and both completed method-contract checks pass; an earlier duplicate method-contract run was cancelled.
- PR #8304 was not pushed after its current-main rebase attempt: with exact required sibling data hydrated, 8/14 tests fail because receipts in current main no longer match the package's frozen classifications/input manifest. Preserve the original remote branch until a separate additive snapshot fix can retain the exact frozen inputs without rewriting its one-shot result.
- At 13:59Z, the direct remote-head listing reported 453 refs, up from 446 at the 13:47Z snapshot. Record the count with its timestamp; the inventory changes while PR work continues.

## 2026-10-07 refresh follow-up (14:18Z)

- PR #8299 refreshed from the stale base onto current main `798ac5ad709168ff1d27b115f10f4f96b126bb71`. Its A13 pre-freeze STOP package is unchanged; all 10 STOP manifest entries verify from Git blobs. The current analysis index passes at 769 directories, and the consumed candidate was not rerun. Workspace-index, analysis-index, replay-gate, and public-navigation checks pass; two method-contract jobs pass and one remains in progress.
- PR #8303 refreshed onto the same main. Its SQLite experiment package remains byte-identical to the original branch; its 30-entry frozen Git-blob manifest and current analysis index verify. A Windows local test rerun hit temporary SQLite file locks; original macOS test results remain recorded. Workspace-index, analysis-index, replay-gate, public-navigation, and two method-contract results pass; one duplicate was cancelled and one is still in progress.
- Fresh inventory: 393 open PRs, 345 targeting main, 323 of those with stale base SHAs; 48 are stacked. Direct remote-head listing: 460 refs. Counts are time-sensitive and changed during this cleanup; do not bulk-rebase stacked work.
## 2026-10-07 refresh follow-up (14:26Z)

- PR #8301 refreshed onto current main `798ac5ad709168ff1d27b115f10f4f96b126bb71`; current head `7951d1996a6de31af505e595eacb3e07d69797ca`. A13B's frozen package and all outcome files are unchanged; the analysis index adds A13B while retaining A09–A13. Static analysis-index (769 entries) and diff checks pass. Candidate/environment/auditor were not rerun because this result is explicitly one-shot.
- Current-head checks: public-navigation, research-workspace-index, replay-gate pass; analysis-index and three method-contract checks are still running. PR remains open for independent review; no reviewer was requested and no merge was attempted.

## 2026-10-07 live inventory follow-up (14:31Z)

- Current `main` is `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d` (includes merged PR #8307). Open PR inventory: 394 total; 346 target main, 48 are stacked; 344/346 main-targeted PRs record an older base SHA; 45 are ready for review. These counts are a point-in-time capture; do not bulk-refresh stacked or frozen-input experiments.
- Direct `git ls-remote --heads origin` returned 461 refs before the retirement below. PR #8307 is merged; its exact head `61d20e52b8d20cc2ba8247d8cbce15ad935a5f73` is an ancestor of current main, branch protection is false, no open PR head/base depends on the ref, and no worktree owns it. Deleted `rescue/windows-pipe-7446-7456-evidence-currentmain-20261007` with an expected-tip lease. The archived evidence remains reachable from main.
- PR #8301 current-head checks for `7951d1996a6de31af505e595eacb3e07d69797ca` are all green (7/7). It remains open for independent review; no merge or reviewer request was made.
- Sampled oldest-updated open PRs include explicit HOLDs, source-bound evidence and unresolved successor dependencies; they are preserved rather than closed or deleted without a full dependency/evidence audit.

## 2026-10-07 rescue refresh follow-up (14:40Z)

- PR #7860 was the explicitly designated canonical successor to closed-unmerged #7862. Refreshed its nine-commit branch from base `69dd261430cb1ed875f5a76411c4a2a54777c114` onto current main `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`; new head `4582378afab9bb7dcdfa273baa50272585e9ad77`. The retained FREEZE/RAW_OUTPUT/RESULT/audit package and the changed source/test blobs are byte-identical to the original #7860 tree. Local saved-only audit passes; 14/14 Windows tests pass normally and under `-O`; diff check passes. Initial CI replay-gate and research-workspace-index pass; further checks may still be pending.
- #7860 remains Draft pending fresh independent content and application review. No reviewer request or merge was made. The 1 ms cadence's explicit HOLD from #7456 remains documented. Keep #7862's original branch until this canonical PR is reviewed and integrated, as its closure note requires.
- Refreshing #7860 makes one additional of the 346 main-targeted open PRs current-base; other stacked and frozen-input branches remain individually gated.

## 2026-10-07 unpaired branch inventory (14:44Z)

- At capture, `git ls-remote --heads origin` returned 462 refs and GitHub listed 396 open PRs. Comparing remote head names with open PR head refs left 65 branches not attached to an open PR.
- Queried GitHub's all-state PR association for each of those 65 exact head names: 39 are attached to closed-unmerged PRs, 26 have no associated PR found, 0 are merged PR heads, and 0 lookups failed. All 65 exact branch tips and association results are in [the per-branch snapshot](BRANCH_ORPHANS_20261007_1450Z.csv).
- None of the 65 is safe for automatic deletion based on this evidence: closed-unmerged branches may preserve unique fixes/evidence, and branches without PR records need provenance, worktree, protection, and dependency review. Keep the branches until individual rescue/retirement dispositions are verified. This capture is a point-in-time inventory, not an abandonment finding.

## 2026-10-07 #6576 A04 rescue refresh (14:58Z)

- Refreshed Draft PR #8284 onto current main `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`, head `8147f74226d85a6354b4cfd45d1986345d1f6ae2`. Its 16 evidence-package files are byte-identical to the prior rescue PR tree; the A04 link is restored in the retained-construction README. Strict analysis index (768 entries) and diff check pass. No experiment candidate was rerun.
- Audit disclosed material source limitations: the original 2,925,419-byte formal raw is absent, and invoking the retained `audit.py` fails with SyntaxError at line 59. These limitations are explicit in the PR description; its original recorded first result remains untouched. Current-head checks: research-workspace-index, public-navigation, replay-gate, analysis-index and one method-contract pass; two method-contract checks are still running.
- The source branch `research/6576-runtime-envelope-a04-20261006` is retained. Although the refreshed PR carries byte-identical package files, its rebased history does not contain the exact source tip `26297fd212179493743aedfa65ba90f81351f94d`; expected deletion guard refused to retire that provenance ref. The source branch has no worktree owner, protection, or open PR head/base dependency, but its source commit identity remains useful until an explicit ancestry-preserving disposition is made.

## 2026-10-08 refresh follow-up

- Current `main` remains `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`. The 2026-10-07 15:01Z snapshot recorded 396 open PRs (348 target main, 48 stacked), 342/348 main-targeted PRs with stale base SHAs, 46 ready, and 462 remote heads. Treat these as timestamped counts, not current inventory.
- PR #7109 is refreshed onto that main at `8394ab7f4a82cafc29a851c28afd56d7a1c8f804`. Exact comparison against its original PR tree found 261/261 paths and identical blobs; strict analysis index (768 entries) and diff check pass. No source experiment or audit was rerun. All commits have `[skip ci]`. The PR remains Draft; no reviewer request or merge was made. Its original review gates remain: fresh same-digest approvals, source/platform/sender qualifications, and independent review. Attempts to update its stale description through the GitHub connector returned Internal error; `gh auth status` reports no GitHub login. Head/base metadata is current; do not claim the description was updated.
- PR #8284 remains Draft at `8147f74226d85a6354b4cfd45d1986345d1f6ae2` on current main. Its package is preserved and its recorded source limitations remain explicit. Current checks previously passed except for a method-contract run whose checkout job was stuck at `actions/checkout@v4` since 2026-10-07 14:55:58Z (run `37640832591`, check suite `112859032948`). No experiment rerun, reviewer request, or merge was made; the original source branch is retained because its exact tip is not an ancestor of the refreshed PR.

## 2026-10-08 orphan recheck

- Fetched current `main` at `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`; `git ls-remote --heads origin` reports 464 heads. The exact PR refs for #7109 and #8284 still match refreshed heads `8394ab7f4a82cafc29a851c28afd56d7a1c8f804` and `8147f74226d85a6354b4cfd45d1986345d1f6ae2` respectively.
- Rechecked all 65 exact tips from `BRANCH_ORPHANS_20261007_1450Z.csv`: all commit objects resolve, none is an ancestor of current main, and none has a tree identical to current main. This does not establish whether a branch is still used by an active worktree or has an external dependency; no orphan branch is cleared for deletion by this check.
- GitHub REST/checks and web reads returned HTTP 500/cache-miss errors; `gh` remains unauthenticated. The ledger push was rejected with GitHub HTTP 500 twice in the prior turn and once again on this recheck, while remote maintenance tip remains `eb1e7889778296995e6a5134ea88a579003c887d`. New local audit note retained in this checkout until GitHub write access recovers.

## 2026-10-08 recovered GitHub read/write follow-up

- The GitHub connector now returns live PR and Actions data. PR #8284 remains open/Draft at the recorded current-main head. Its formerly stalled workflow run `37640832591` is terminal `cancelled`; checkout was cancelled and all later steps skipped. The other six PR-triggered workflows for that head completed successfully. No experiment rerun was performed.
- Updated PR #7109's stale description in place. Replaced only the obsolete refresh sentence with current base `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`, head `8394ab7f4a82cafc29a851c28afd56d7a1c8f804`, exact 261-path/blob preservation, strict index and diff-check results, and the reason no CI was started (`[skip ci]`). Preserved the experimental record and fresh same-digest review requirements. PR remains open/Draft; no review request or merge.
- Push recovered: commits `abeeda822071` and `6c8dc9af70d7` are now on `maintenance/inventory-current-main-20261006`, whose verified remote tip is `6c8dc9af70d7a69d97235f59e9934dc0fe5a6912`.

## 2026-10-08 #8284 additive audit repair

- The Actions connector confirmed the previously stalled run `37640832591` is terminal `cancelled` (checkout cancelled; remaining steps skipped); six other PR-triggered workflows for old head `8147f74226d85a6354b4cfd45d1986345d1f6ae2` succeeded.
- Preserved frozen `audit.py` unchanged and verified its exact bytes are identical on the original source ref and prior PR head (SHA-256 `69a21440bdb28d73cf764006350381b1222e5d458bb93fd547c0f220d17811a1`). Discovered the checked-in `SHA256SUMS.source` expected hash `8c426b37f9e8723ec1b715610a6f914e37a0f8951a5e9c2076f5c8b09ef20080` does not match either ref; this pre-existing provenance discrepancy is recorded, not silently corrected.
- Added `audit_cli_repaired.py` as an additive copy changing only the malformed CLI output newline and `AUDIT_REPAIR.md` documenting the hash mismatch and validation boundary. Python AST parse, `--help`, and diff check pass. The formal audit was not run because the original 2,925,419-byte raw is absent; no candidate, stored result, or scientific conclusion was rerun or rewritten.
- Fast-forwarded Draft PR #8284 to head `0ac1368b7520f75208bfc793f9dab228586f1b4e` on current main `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d` with `[skip ci]`. Updated and read back the PR description with the repair, hash discrepancy, and missing-raw limitation. No reviewer request or merge was made.
