# Audit repair 01 — singleton JSON array handling

The first independent PowerShell readback retained in `AUDIT_ATTEMPT_01.json`
verified the 56 source snapshots, the materialized source tree, all three
startup route outputs, source hashes, and the raw-owner mismatch. It returned
exit 1 only on `first_environment_stop_preserved`: PowerShell's
`ConvertFrom-Json -AsHashtable` represented the one-element `run-status.json`
array as a hashtable, so the audit checked its property count (2) instead of
array length (1).

Repair 01 wraps that JSON conversion in an explicit array and writes a new
readback to `AUDIT_REPAIR_01.json`. It changes no candidate source, frozen
input, or startup result. The candidate is not rerun.
