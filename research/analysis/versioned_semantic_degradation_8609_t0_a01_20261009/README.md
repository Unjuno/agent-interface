# Issue #8609 T0 A01 — versioned semantic degradation

This package evaluates a finite, authored interface contract under independent service failures. It compares an all-or-nothing route with a versioned selector that preserves only operations whose declared guarantees remain available. Candidate output is eligibility and claim-ceiling data only; it does not dispatch GUI input, create authority, or claim task effects.

See `PROTOCOL.md` for the preregistered hypothesis, 1,024-case matrix, decision rule, and limitations. `ENVIRONMENT.md` preserves the pre-freeze OrbStack read failure and runtime choice. `FREEZE.json` binds source/input hashes and the host runtime. `RUN_RECORD.json`, candidate raw output, and the independent audit retain the one formal run.
