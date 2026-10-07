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
- [Current branch tips](BRANCH_TIPS_20261007_123127Z.csv) records 449 remote branches from one ls-remote response.

- Current PR activity capture: 379 open (335 Draft, 44 ready), 86 updated within 24 hours, 110 within 48 hours, and 130 created over 3 days earlier. This is not an abandonment test; STOP/HOLD evidence and stacked PR dependencies need preservation review. See [activity summary](OPEN_PR_ACTIVITY_20261007_123440Z.md) and [all 379 PR rows](OPEN_PR_ACTIVITY_20261007_123440Z.csv).

- The author deleted fix/x11-explicit-up-01a0ff2c on Oct 7 at 12:34 UTC. Its PR #7114 is closed unmerged and explicitly titled Superseded; the remaining branch delta is three test-file edits and is not integrated. Do not restore or adopt that V2 change. The historical evidence archive was separately rescued by merged PR #7980 (commit 5d896208724f824b7a0490a512bc72340a80bf0d), whose tip is reachable from main and whose MANIFEST.json is present there.

## Follow-up policy

1. Triage the 65 unpaired, non-main-ancestor branches individually. First identify merged/closed PRs, ancestry and stack dependencies, worktree ownership, evidence custody, and whether each unique change is already integrated. Delete only verified aliases or fully integrated disposable refs; rescue useful evidence to a current-main PR before removing its source ref.
2. Review the 335 Draft PRs for active stacks, explicit STOP/HOLD allocations, and duplicated or superseded work. Preserve each live stack's base/head relationship.
3. Prioritize ready PRs with passing checks for maintainer review. Do not merge on inventory evidence alone.
4. Re-run the complete inventory after these dispositions; this snapshot does not claim the repository is clean or that all 65 unpaired branches are abandoned.

## Snapshot files

- [Open PRs](OPEN_PRS_20261007_121116Z.csv)
- [Branch tips](BRANCH_TIPS_20261007_121116Z.csv)
- [Branch-to-open-PR crosswalk](BRANCH_CROSSWALK_20261007_121116Z.csv)
- [Unpaired-branch triage](BRANCH_ORPHAN_TRIAGE_20261007_121116Z.csv)