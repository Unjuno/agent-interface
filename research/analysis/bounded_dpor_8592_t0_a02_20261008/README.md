# Issue #8592 T0 A02 — bounded DPOR validation

**Formal status: pending preregistered one-shot execution.** This successor allocation follows A01's execution-integrity STOP (WSLc individual-file binding treated the runner path as a directory; candidate did not start). A02 keeps the frozen method and fixtures, uses a separate candidate-only directory mount, and will not retry A01. This package tests a finite sleep-set DPOR schedule explorer against an independently implemented exhaustive oracle. Construction results are not formal results. No GUI, model, network, real actuation, user, or application is involved.

Read the frozen [H/T/D/C/U protocol](PROTOCOL.md) before interpreting any result. The only permitted positive conclusion is method-scoped equivalence on the two authored finite cases; requested WSLc memory limits were not kernel-enforced and no runtime-speed or live-safety claim is authorized.

Files:

- `candidate.py`: candidate sleep-set DPOR and deterministic finite transition model.
- `auditor.py`: separate exhaustive-permutation, reachable-prefix diamond, and raw-only replay oracle; imports no candidate implementation.
- `input.json`: public lifecycle and commuting-control fixtures.
- `truth.json`: auditor-only expected gates and mutation controls.
- `test_*.py`: construction and audit-corruption tests; no formal output is produced by these tests.
- `CANDIDATE_FREEZE.json`: candidate-visible source/input hashes only; contains no hidden truth or auditor hash.
- `FREEZE.json`: complete byte hashes, runtime identity, base and allocation metadata; generated before formal execution and visible only to the auditor.
- `results/`: exclusive-create formal candidate/audit output, checksums, and report.

External prior art: Cormac Flanagan and Patrice Godefroid, [“Dynamic Partial-Order Reduction for Model Checking Software”](https://doi.org/10.1145/1040305.1040315), POPL 2005. DPOR is established prior art; this package claims only a repository-scoped, independently audited bounded comparison.
