# Issue #4945 allocation-02 — construction STOP

## Disposition

The one excluded Docker construction invocation ran the frozen 40-cell representative matrix and 10 identity/type controls, then the independent auditor returned `HOLD_AUDIT_INTEGRITY` (exit 1). Under Issue #4945's gate, the allocation stops here: **formal invocations = 0**. Do not rerun this allocation, patch its source, or treat construction observations as a formal/scientific result. Allocation #3991 DELETE results and the prior #4927 STOP remain unchanged.

## Executed evidence

- Image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`; requested linux/amd64 on OrbStack linux/aarch64; network none, source/root read-only, 0.25 CPU / 256 MiB / 32 PIDs.
- Runtime recorded CPython 3.13.5 / SQLite 3.40.1 / x86_64.
- One construction wrapper invocation; 50 per-case raw directories (40 process-exit cells and 10 identity controls), 4.6 MiB retained. Exact per-case database, journal/WAL/SHM snapshots and JSON manifests are under `evidence/construction-01/construction/raw/`.
- `RESULT.json`: 40 construction rows, 10 control rows, one wrapper invocation. `AUDIT.json`: HOLD, 21 errors. Its summary observed `EFFECT_FIRST` AFTER_FIRST duplicate 2/2, `ATOMIC_EXTERNAL` AFTER_FIRST duplicate 2/2, `RECEIPT_FIRST` false completion 2/2, and `ATOMIC_LOCAL` exactly once 10/10 across the two modes.
- No unit/corruption suite ran: `construction.sh` stopped on the failing audit because it uses `set -e`.

## Failure analysis

The audit is not eligible to accept the data. It incorrectly applies the formal 120-row / 30-control matrix cardinalities to the expressly excluded 40-row / 10-control construction matrix. Separately, its expected retry policy treats every protocol's `AFTER_SECOND` as retryable. For split protocols both independent commits have already completed at that cut, so receipt-only status must be `COMPLETED` and retry must be forbidden. (For `ATOMIC_LOCAL`, `AFTER_SECOND` is still before the shared commit and retry is allowed.) The runner and raw state therefore cannot be promoted from the auditor's partial counters.

This is a construction/auditor design STOP, not a scientific contradiction or evidence against WAL. No formal row was started. Any correction must be frozen under a new successor allocation and run with fresh storage/identities; these 50 construction cases are not pooled or reused.
