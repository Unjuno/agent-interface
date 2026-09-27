# Formal allocation record

Status: `STOP_AUDITOR_IMPLEMENTATION_DEFECT`; no scientific verdict.

The frozen trainer was invoked once for the three preregistered seeds. Its raw outputs and worker inputs are retained in `training/<seed>/`. The separate frozen auditor was invoked once, exited 1 with a `KeyError` caused by a stale summary-field name, and did not write `AUDIT.json`. No retry, auditor patch, or trainer rerun is permitted for this allocation.

See `FORMAL_STOP.json` for the exact stop record and byte-level hashes. The numbers in that record are descriptive outputs, not an adjudicated treatment result. The Docker named volume `unjuno-needle-single-query-ack-4732-formal-v1` is retained and must not be deleted.
