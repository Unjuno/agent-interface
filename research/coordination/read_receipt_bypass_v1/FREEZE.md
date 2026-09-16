# Read-receipt bypass v1 — source-first freeze

Task `COORD-READ-RECEIPT-BYPASS-20260916-019`, Issue #508.
Publication base `d95d90899686c99061f14bdd259797c0b3984f13`.
Formal allocation `read-receipt-bypass-20260916-a1`: exactly four first outcomes; rerun budget 0.

Single factor: `tracked` routes A and B through `ReadTracker`; `bypass` routes A through the same tracker but reads task-relevant B by direct SQLite query. Decision, mutation, and the single-transaction owner revision-check + generation commit are otherwise fixed. No formal case runs before GitHub blob readback matches construction bytes.
