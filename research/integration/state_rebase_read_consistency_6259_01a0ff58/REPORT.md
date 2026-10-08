# Predicate read consistency after ambiguous delivery (#6259)

One new private Windows CPython3.11.9/SQLite3.45.1 construction ran six fresh
WAL databases once. Required target=X and forbidden collateral=0 were read
separately across a controlled atomic UPDATE from (X,1,g0) to (Y,0,g1).
Neither actual state satisfied both predicates. Split reads falsely accepted
one mutated case; one read transaction and generation joining refused. All
three stable controls refused. Separate raw-only audit exited0, and this packet
reader verifies each original closed DB hash and reads only fresh private copies.

This is a transfer of established snapshot semantics, not a new isolation
mechanism. One snapshot or atomic generation checking is sufficient for this
finite consistency boundary. Snapshot consistency does not establish freshness;
generation checking requires every relevant writer to atomically update it.
No request origin, replay permission, physical input, GUI/model/task success,
performance or production-backend claim. Existing #6259 eight-case T0 and
browser STOP evidence were not replayed or altered.

Prospective issue comment5971521680 and first result5971526822 bind the scope.
Original candidate/auditor tool exits0 and elapsed times0.2952887/0.2177674s
were observed, but native PID and exact UTC endpoints are unavailable. No
reconstructed timing is claimed. These are construction receipts, not formal
scientific allocation provenance. Frozen candidate SHA is in FREEZE.json;
the independent auditor was present before execution but its hash was not
included in that freeze. This incomplete provenance remains explicit.

All code snapshots have .py.txt suffix and are inert; DBs are base64. Restore
only into new private copies for inspection. Never rerun the consumed assay
directory. No runtime, workflow, dependency or index change is included.
