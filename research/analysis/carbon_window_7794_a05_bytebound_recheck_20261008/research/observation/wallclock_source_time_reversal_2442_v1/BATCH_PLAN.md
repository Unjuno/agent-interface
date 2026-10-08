# Allocation 02 — execution-envelope-only batching successor under #2442

The consumed allocation-01 remains `STOP_OUTER_TOOL_TIMEOUT_INCOMPLETE_DENOMINATOR` with no same-ID rerun. Allocation 02 is `wallclock-source-time-reversal-2442-20260922-02-batches`.

Scientific H/T/D/C/U, 34 cases, case order, candidate, producer, 1 px / 2 px bounds, 73 px/s speed, age thresholds and failure labels are byte-identical to allocation-01. No allocation-01 result is pooled. The only delta is outer execution serialization:

- batch0: case indices [0,9), 9 fresh producer lifetimes;
- batch1: [9,18), 9;
- batch2: [18,26), 8;
- batch3: [26,34), 8.

Each batch is a separate first-outcome invocation with a new raw directory and Xvfb lifetime. A missing/nonzero/incomplete batch stops allocation-02; no replacement or repeated batch. Aggregate scientific evaluation occurs only after all four batch endpoints are zero/complete. `audit_batches.py` verifies the four batch terminal receipts and exact case identity, constructs a read-only aggregate view, then invokes the already frozen independent `audit.py` plus its 10 corruption controls. The aggregate view is not new experimental data.

No thresholds, source-time semantics, stress conditions or outputs were changed after allocation-01 partial outcomes. This batch change addresses only the observed outer tool envelope and is not evidence in favor of the hypothesis.
