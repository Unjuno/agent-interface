# Auditor v1 finding and repair

The first independent audit returned `FAIL` with `pair_reconstruction`. It independently derived the same two identities and timestamps, but serialized them as one `times` list while the candidate result used named timestamp fields. The failure was in the audit's representation comparison, not the raw event identity or timestamp values. The exact first stdout is retained in `AUDIT_FIRST.stdout.txt`.

`audit.py` was corrected to emit the same named fields from its separate raw-only implementation. Neither `RAW.json`, `join.py`, `run.py`, nor the original `RUN.stdout.txt` changed for this repair. The corrected raw audit returns PASS scoped and still records missing independent task-effect rows as HOLD.
