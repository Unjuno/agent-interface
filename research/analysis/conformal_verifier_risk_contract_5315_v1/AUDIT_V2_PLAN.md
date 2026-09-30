# Auditor successor — unchanged Issue #5315 allocation-01 raw

The only defect in audit attempt 01 was its `altered_outcome` self-control, which assigned `true` to a field already true in the selected raw row. The one-shot formal allocation and audit-01 output remain byte-for-byte unchanged.

Auditor v2 changes the mutation to invert the existing Boolean, recomputes all 20,000 row outcomes using the already-frozen candidate-independent row checker, reconstructs receipt aggregates and finite-sample expectations, verifies the original auditor source hash, and runs in a fresh network-disabled container process. It reads the same frozen raw/receipt and writes only `audit-02.json`. It does not call `run.py`, generate new rows, or rerun a formal allocation.

Decision: accept the statistical unit only if audit v2 exits 0, all frozen source/raw hashes match, every row and aggregate reconstruct exactly, Monte Carlo rates meet the original ±0.015 gates, and all three mutation controls are detected. Preserve audit attempt 01 as FAIL regardless of v2 outcome.
