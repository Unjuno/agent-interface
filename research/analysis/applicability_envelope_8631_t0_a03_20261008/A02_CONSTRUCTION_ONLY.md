# T0 A02 — corrected CLI, hand-authored boundary (construction only)

Fresh input relative to the A01 STOP. Candidate and auditor each invoked once and exited 0. The auditor reconstructed 9/9 checks with zero errors; 4/4 output-integrity invariants were reported. However, A02 used a hand-authored predicate rather than a learned boundary and therefore did not test the core learning hypothesis. Its result is construction-only; it is not a PASS for Issue #8631 and its rows are not reused by A03.

- Candidate stdout SHA-256: `F675A290AA604CF36060BEB37ADBB50DF4A3B60D5102E72E81067ABC8D07A5D4`
- Fixture SHA-256: `69C3B93BDA7040246172ED6C3ADA4760EE11546A0B55D8552E1E4C986A89A0FB`

No candidate retry or result relabeling. A03 is separately frozen with its own fixture and an actual finite conjunction learner.
