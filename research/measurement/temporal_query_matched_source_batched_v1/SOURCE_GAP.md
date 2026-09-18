# #1498 source-retention boundary

Issue #1498 records construction and source SHA-256 values for `PLAN.md`, `experiment.py`, and `audit.py`, but its declared additive source path is absent from the retained branch and current main. The branch `research/temporal-query-matched-source-preflight-1498` is fully contained in main and has no unique files/commits; direct contents lookup of the declared path returns 404.

Therefore #1501 does **not** claim byte reuse of #1498 implementation. It independently reconstructs the semantics frozen in #1498/#1501: same immutable history source and evidence budget for both arms, four later-revealed request classes, a class-blind fixed schedule, class-aware after-the-fact query selection, no future/cross-scope/budget/authority leakage, and the same >=15 percentage-point aggregate gate. This source gap is an evidence-retention limitation, not a scientific result.
