# A2 premeasurement freeze

Allocation: receiver-concurrent-identical-20260916-a2.
Antecedent A1 is retained INCOMPLETE_SUPERVISION_TIMEOUT; no A1 case ID is reused.

Experiment semantics remain byte-identical to freeze bf03e799 for receiver.py, worker.py, run.py and audit.py. A2 changes only allocation IDs, outer supervision split into six sequential 5-case invocations, and the mutation-driver no-op repair in test_audit_v2.py.

Master schedule: d001..d030, alternating launch order a,b then b,a. Chunks are exactly consecutive rows: d001-d005, d006-d010, d011-d015, d016-d020, d021-d025, d026-d030. The exact master/chunk SHA-256 hashes are in A2_PREREG.json. Each chunk uses unchanged run.py into a fresh output root. Chunks are combined offline in master order only after all six complete; combining performs no receiver execution.

Decision gates are unchanged from A1. All 30 rows must independently audit PASS. No same-ID rerun, replacement, extension or timeout tuning after measurement begins.
