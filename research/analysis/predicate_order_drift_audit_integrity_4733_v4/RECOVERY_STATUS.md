# Recovery status — Issue #4956

Exact-content archive of the four source/freeze files from remote branch
`research/predicate-order-audit-hardening-4956-20260928`, source tip
`c91018b5e970a5861dcea89ec3480b08a3396036`. No original file was edited.

Issue #4956 records one host-only standard-library validation. Source/archive
identity and four frozen unit methods passed, then the unchanged 336-row
baseline was rejected by exact floating-point weight equality before the
predecessor auditor, mutation controls, or independent post-run checks ran.
The recorded disposition is `HOLD_VALID_BASELINE_REJECTED`: the predecessor
serializes weights rounded to 12 decimal places, so exact comparison was too
strict. No scientific predicate-order outcome was produced; no retry was made.
The independent successor #4959 addresses this with a separately frozen
absolute tolerance and preserves this HOLD unchanged.

This archive did not run the auditor, tests, extraction, or any experiment. It
is preservation of the source and protocol only, not validation or promotion.
