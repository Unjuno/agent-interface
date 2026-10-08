# CI history for the additive T5 package

All times UTC, GitHub Actions evidence retained on the PR branch.

1. At head `1fcaf30079010790f6d202faaf11a5d5406247ea`, `analysis-index`
   **failed** (run `36743703436`). Its exact diagnostic was: “Generated
   analytical result index is stale. Generated entries no longer qualify as
   retained results/failures: research_failure_detector_5531_t5.” The package
   directory had been added to the generated index before the required
   `REPORT.md` existed. `public-navigation`, `research-workspace-index`, and
   `replay-gate` succeeded at that head.
2. The additive repair added `PLAN.md` and `REPORT.md`, retaining the exact
   experiment scope and making the directory qualify under
   `research/analysis/check_index.py`. No experiment or raw artifact changed.
3. At head `acccb4495bead608e0773fc9b0925fdf51536faf`, all four checks passed:
   `analysis-index` (run `36744069430`), `public-navigation` (run
   `36744069414`), `research-workspace-index` (run `36744069548`), and
   `replay-gate` (run `36744069586`).

The failed run remains visible in Actions and is not relabeled. The current
success is scoped to repository integration/format checks; it does not upgrade
the experiment beyond its host-only synthetic scope.
