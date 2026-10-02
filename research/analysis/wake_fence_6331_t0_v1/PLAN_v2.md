# Issue #6331 T0 allocation-02 frozen plan

This is a distinct allocation after allocation-01 stopped before candidate invocation because `origin/main` advanced after freeze. Original freeze and STOP remain immutable. Current source base and hashes are in `FREEZE_v2.json`; test matrix and decision semantics are unchanged from `PROTOCOL.md` and `fixture.json`.

Immediately before execution require `origin/main == source_base`, exact Lease/candidate/auditor/fixture hashes, cached image ID/platform, responsive OrbStack Docker, and empty `results/formal-02/`. Candidate once; independent auditor once after candidate exit 0; retries 0. Candidate receives only the exact runtime Lease source and fixture. Auditor receives only fixture and candidate raw. Record command, exit, stdout/stderr, outputs and all hashes. Any changed gate before candidate invocation is a prelaunch STOP and gets a new successor allocation; after candidate invocation preserve the outcome without retry.
