# Effect/receipt transaction scope across SQLite journal modes

Successor allocation `effect-receipt-wal-vs-delete-3991-20260928-03` for
Issue #4945, following the preserved construction STOPs in #4927 and allocation
`...-02`. The excluded construction audit uses separate denominators (50 vs
150) and protocol-specific retry expectations at `AFTER_SECOND`. This directory
contains a fresh synthetic experiment; it does not alter or pool predecessor
evidence.

The question is whether process-exit recovery in SQLite DELETE and WAL modes
changes the boundary between an application effect and its completion receipt.
The fixture is private and standard-library-only. See `PLAN.md` for the frozen
H/T/D/C/U, matrix, gates, commands, and limits. Source freeze and the first
construction result are recorded on Issue #4945 before any formal run.

No result in this directory is a product-runtime or distributed exactly-once
claim.
