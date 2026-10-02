# Issue #6680 A01 — local CI record

Local verification on the refreshed research branch completed before publication.

- `python research/analysis/check_index.py`: PASS, 558 retained result/failure directories indexed.
- The #6680 package construction suite: 28/28 tests PASS.
- All other test suites selected by the current `.github/workflows/analysis-index.yml`: 114/114 tests PASS across the listed packages, including the five-test #6451 suite added on latest main; no GitHub-hosted workflow was modified.
- Combined local test total: 142/142 (the 28 #6680 construction tests plus 114 workflow-selected tests).
- The workflow's frozen-source provenance check: PASS; commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` reproduces SHA-256 `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`.
- `git diff --check`: PASS.

The local reproduction followed the workflow's declared working directory for the nested #6492 suites and restored its frozen workflow source in a temporary archive for the #6590 geometry suite. Initial orchestration from the repository root omitted those workflow contexts and produced harness-path/hash mismatches; the exact workflow invocations then passed. No formal candidate or auditor was rerun for this correction.

At the time of this initial publication record, the GitHub Actions checks for the PR head had not completed; local CI was reported separately from those remote checks.

## Latest-main local rerun — 2026-10-03

After merging current `origin/main` (`b573071d821e20e818304200a9e6ec8c9bbf5670`), the scoped local CI was rerun against the merged tree. `python research/analysis/check_index.py` passes with 565 indexed result/failure directories. The #6680 package remains 28/28. Every test command selected by the latest `.github/workflows/analysis-index.yml` passes: 119/119 tests, including the newly selected #6749, #6590 design, #6617, #6604, #6581, #6650, #5370 and #6451 suites. The separate workspace-index tests pass 21/21, and `python research/check_workspace_index.py --git-tree` reports 156 reachable top-level research directories. Public navigation passes on the full checkout: 26 documents and 1,586 repository-relative links. `git diff --check` passes.

For the #6590 provenance-dependent tests, the CI's frozen workflow restore was reproduced in a temporary source archive; its SHA-256 is `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`, as expected. The nested #6492 corruption-control test was run from its workflow-declared working directory. An initial local invocation without those CI contexts produced harness-only failures (current workflow hash and missing package import path); exact-context reruns passed. No research source, frozen raw, candidate, or audit output was changed or rerun.

At this local-rerun checkpoint, GitHub checks on PR #6724's prior head had remained queued since 2026-10-02 19:21 UTC. The latest-main branch update was then pushed as `0ecb4ab2d99fa76502b7f8ea84f4c6ac94a20e09`, creating six new checks; all six still reported `QUEUED` when PR #6724 merged. GitHub recorded merge commit `80e0d41b2dd6f56b0a55cd004f0ad10a6275448e` at `2026-10-02T19:43:30Z`. Therefore the evidence is the passing local CI listed above; no GitHub Actions check is claimed as green or completed.
