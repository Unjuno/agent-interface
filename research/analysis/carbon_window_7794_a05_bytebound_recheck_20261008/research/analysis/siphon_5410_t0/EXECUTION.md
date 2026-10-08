# T0 execution record

- Formal candidate: one network-disabled OrbStack Docker invocation; no RNG or retry.
- Raw result: `raw/formal.json`; 28 policy/scenario traces.
- Disposition: FAIL. The two-tick beta lease causes repeated expiration/reacquisition; SCC guard and reachability oracle each leave one workflow incomplete at tick 40. This violates the preregistered zero-deadlock gate.
- Independent raw trace audit: confirms resource ownership/release invariants but returns FAIL on the guarded-policy liveness predicate.
- Four corruptions are rejected; outputs and SHA-256 values are in `FORMAL_FAILURE.md`.
- No candidate modification or rerun after observing the failure.
