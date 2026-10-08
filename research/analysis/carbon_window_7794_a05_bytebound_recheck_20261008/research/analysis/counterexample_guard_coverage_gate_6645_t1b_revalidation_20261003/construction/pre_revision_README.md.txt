# Issue #6645 T1b integration revalidation

This additive package checks whether the merged T1b candidate's decisions are invariant to removing outcome-bearing words from row IDs. It does not rerun, replace, or alter the T1b allocation or its retained raw evidence.

- Protocol and frozen decision gate: [`PREREGISTRATION.md`](PREREGISTRATION.md)
- Executed outcome and limitations: [`REPORT.md`](REPORT.md)
- Independent auditor and construction tests: [`independent_audit.py`](independent_audit.py), [`test_independent_audit.py`](test_independent_audit.py)
- WSLc runtime and output-mount preflight: [`results/PREFLIGHT.md`](results/PREFLIGHT.md)
- Original immutable T1b package: [`../counterexample_guard_coverage_gate_6645_t1b_v1/`](../counterexample_guard_coverage_gate_6645_t1b_v1/)

The selected Windows route uses WSLc 3.0.1.0 and a locally cached, digest-pinned Python image, not Docker Desktop. This boundary check is finite and synthetic; it is not a Docker-vs-WSLc performance comparison and does not demonstrate memory-limit enforcement.
