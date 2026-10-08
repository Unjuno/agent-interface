# Issue #6331 T0 allocation-03 frozen plan

Allocations 01 and 02 stopped before candidate invocation because main advanced after their respective freezes; preserve both exact STOP records. Allocation-03 is frozen against `c09f073f2a6e078c0fe5d8192246cc821cecc29c`; all scientific code, fixture and gates retain the hashes in `FREEZE_v3.json`. Matrix/rules remain in `PROTOCOL.md` and `fixture.json`.

Require main exactly at source base, exact source/code/fixture hashes, cached pinned image, responsive engine, and empty `results/formal-03/` immediately before candidate. Run the exact current `Lease` candidate once; if it exits 0, run the separate raw-only auditor once. Zero retries. Retain all raw streams, exits, and hashes. A changed gate before launch means another preserved prelaunch STOP; after launch do not tune or repeat.
