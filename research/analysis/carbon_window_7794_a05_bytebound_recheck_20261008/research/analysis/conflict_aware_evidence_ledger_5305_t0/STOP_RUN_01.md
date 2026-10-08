# STOP record — first independent audit invocation

Date: 2026-09-30. Candidate invocation: 1. Audit invocation: 1.

The candidate exhaustively emitted 31 subsets and raw file SHA-256
`1b59434596847c7ee39de96c7845ee96e02f683325506b41cabf212e7a932f12`.
The auditor compared every row with its separately coded oracle, then stopped
on hard-coded aggregate counts that were wrong (`expected CONFLICT=6`; the
truth table contains 14). No PASS was issued by this invocation. Candidate raw
was not modified. The failed audit source was superseded before the next,
separate audit-only invocation; candidate source and semantics did not change.

Disposition: `STOP_AUDIT_EXPECTATION_MISMATCH`, an analysis/validation harness
defect, not a scientific FAIL and not evidence against the hypothesis. Preserve
alongside the corrected audit result in `audit.json`; do not erase this first
outcome.
