# Issue #6680 A01 — local CI record

Local verification on the refreshed research branch completed before publication.

- `python research/analysis/check_index.py`: PASS, 558 retained result/failure directories indexed.
- The #6680 package construction suite: 28/28 tests PASS.
- All other test suites selected by the current `.github/workflows/analysis-index.yml`: 114/114 tests PASS across the listed packages, including the five-test #6451 suite added on latest main; no GitHub-hosted workflow was modified.
- Combined local test total: 142/142 (the 28 #6680 construction tests plus 114 workflow-selected tests).
- The workflow's frozen-source provenance check: PASS; commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` reproduces SHA-256 `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`.
- `git diff --check`: PASS.

The local reproduction followed the workflow's declared working directory for the nested #6492 suites and restored its frozen workflow source in a temporary archive for the #6590 geometry suite. Initial orchestration from the repository root omitted those workflow contexts and produced harness-path/hash mismatches; the exact workflow invocations then passed. No formal candidate or auditor was rerun for this correction.

The GitHub Actions checks for the updated PR head must still complete before merge; local CI does not substitute for those remote checks.
