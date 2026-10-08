# Local CI record

The commands in `.github/workflows/analysis-index.yml` were run locally with
Python 3.12. The workflow's provenance step was mirrored first: the frozen
workflow from commit `e2e434dd07e1034c5c4303982a0b1ec33ea35cfd` matched expected
SHA-256 `b19000e027e7379ef6c0122e3f8cfd0b2faacb4c54d985ab87d27c1be914f7c2`.
`research/analysis/check_index.py` passed with 591 retained result/failure
directories. All 21 existing workflow unittest suites and the added S06
construction suite passed; S06 itself passed 3/3.

The S06 construction suite is now also an explicit step in the Analysis Index
workflow so the PR's GitHub Actions run covers the new package.

The first local attempt ran the provenance-sensitive tests before emulating the
workflow's frozen-source restore, so two pre-existing #6590 tests failed only
on the root workflow hash (`879690...` observed versus the pinned `b19000...`).
After matching the workflow's documented restore behavior, the full listed suite
passed. The working-tree workflow was then restored to its branch version and
the S06 construction-test step was added for this PR.

The scoped experiment outcome is separately established by the one-shot
OrbStack candidate and independent auditor in `RUN.json`; local CI is not used
as scientific evidence.
