# Immutable run log

## Run 01 — 2026-09-30, host Python 3.11.9

Command: `python formal.py` followed by `python audit.py` from this directory.

Candidate completed all 31 subsets. Raw SHA-256:
`1b59434596847c7ee39de96c7845ee96e02f683325506b41cabf212e7a932f12`.
The first audit exited nonzero on a frozen expected-count assertion. No PASS
was claimed and no candidate raw was changed. The candidate output itself was
retained unchanged as `raw.json`; the mismatch was in the audit's hand-written
aggregate expectations, not a candidate-vs-oracle row discrepancy.

Disposition: `STOP_AUDIT_EXPECTATION_MISMATCH`. The initial gate was not met.

## Run 02 — corrected auditor over the exact Run 01 raw

This is a distinct read-only audit invocation, not a rerun of the candidate.
Correction: derive the combinatorial counts from the five-atom truth table;
move the duplicate/freshness mutations to rows representing those cases. The
candidate source, raw bytes, and frozen semantics are unchanged. The corrected
audit validated all rows against a separately coded oracle and rejected four
altered copies, producing the scoped finite-model PASS.
