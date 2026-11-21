# Issue #57 effect receipt handoff — current-main regression

At `3d1ce3abeceda889f4e1004d3c7fdfa93e0f006c`, the existing research-only adapter and comparison validator suites pass 42/42 on Windows CPython 3.11.9 normally (1.484 s) and under `-O` (1.641 s).

The gate binds independent score and capture receipts to one task/action/operation/target generation, adjudicates expiry/release/horizon timing, preserves factual success separately from eligible success, and passes the result through the measured-run validator. Unknown or post-horizon effects cannot count as authority-eligible success or correctness-qualified break-even.

This confirms the **offline adjudication seam is implemented and covered**. The adapter itself labels its inputs as retained local evidence. No live standard caller currently supplies a complete identity-bound capture/effect/release/horizon bundle to this adapter, and provider-attempt usage reconciliation remains absent. Therefore this is not live GUI/MAP01 success, recovery reliability, integrated efficiency, or Research Preview graduation. Keep #57 open.

Raw logs, conditions, source hashes, and SHA256SUMS are retained in this directory.
