# A01 typed-signal guard and paired-recovery archive note

This directory preserves the 45-file research package from branch tip
`075aa109c9464a8fcd1b81a35700b231bfda37bc` of
`research/59-early-typed-guard-a01-20261012`. The package was copied as
committed; its candidate attempts, failed expectations, audit outputs,
source snapshots, and SHA manifests remain distinct.

The WSLc typed-monitor construction's final candidate v3 passed 4/4 checks,
and the independent source/result/argv audit exited 0. The CLI mount rejection
and the earlier v1/v2 candidate failures are retained. The result is limited
to the typed-signal monitor boundary. No model, game, Doom process, Executor,
owner thread, OS input, or task effect was used. The separate checked-out
regression run of 37 tests is not a current-main pass because its fixtures
differ from current main.

The package also records a separate offline paired-recovery finding: a fully
validated newer health/ammo pair did not advance `last_pair_sequence` after a
prior hard invalidation. The branch contains a one-line repair and its
regression evidence (1/1 replay and 43 related V39 tests). Those changes are
preserved in the package's `source/pair_recovery/` snapshots; they are not
applied to the runtime files in this archive or represented as integrated
behavior. The historical raw trace is referenced by hash in the finding, not
included here.

This archive contains monitor-boundary construction and offline repair evidence
only; it contains no live/game result or MAP01 effect. Keep the source branch
until the implementation delta and all branch references receive current-main
review.
# A01 typed-signal guard and paired-recovery archive note

This directory preserves the 45-file research package from branch tip
`075aa109c9464a8fcd1b81a35700b231bfda37bc` of
`research/59-early-typed-guard-a01-20261012`. The package was copied as
committed; its candidate attempts, failed expectations, audit outputs,
source snapshots, and SHA manifests remain distinct.

The WSLc typed-monitor construction's final candidate v3 passed 4/4 checks,
and the independent source/result/argv audit exited 0. The CLI mount rejection
and the earlier v1/v2 candidate failures are retained. The result is limited
to the typed-signal monitor boundary. No model, game, Doom process, Executor,
owner thread, OS input, or task effect was used. The separate checked-out
regression run of 37 tests is not a current-main pass because its fixtures
differ from current main.

The package also records a separate offline paired-recovery finding: a fully
validated newer health/ammo pair did not advance `last_pair_sequence` after a
prior hard invalidation. The branch contains a one-line repair and its
regression evidence (1/1 replay and 43 related V39 tests). Those changes are
preserved in the package's `source/pair_recovery/` snapshots; they are not
applied to the runtime files in this archive or represented as integrated
behavior. The historical raw trace is referenced by hash in the finding, not
included here.

This package records the branch's distinct outcomes; it does not authorize a
live/game run or establish a MAP01 effect. Keep the source branch until the
implementation delta and all branch references receive current-main review.
