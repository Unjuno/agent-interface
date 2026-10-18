# Concurrent T0 distinction and publication note

The frozen experiment began from main `c837ad535eed085d95744ad0a9680535a5bb7143`, before the separate #7709 T0/T1 publications appeared. The already-merged PR #7729 is closely related but not the same frozen design. Its 240-per-workload, n=8, fixed four-block, all-null test does not cover this package's n=16 cells, warm-up family, nonzero route effect, 500 replicates/cell, data-driven descriptive segmentation, or explicit no/extra-boundary invariance.

This package is therefore delivered as an additive expanded stress variant for review, not as a correction or replacement of the prior result. It does not change the first T0's historical `METHOD_PASS_SCOPED`, PR #7729, the T1 `HOLD_TOO_FEW_INDEPENDENT_RUNS`, or the T2 allocation gate. The stationary-null detector over-segmentation is retained as a warning; H's coverage comparison is driven by session-level inference and does not validate regime discovery.

The first package commit was built on the frozen-main lineage. Because main advanced during concurrent research, the final review branch is based on the latest observed main and carries this distinction explicitly. No existing branch was force-updated.
