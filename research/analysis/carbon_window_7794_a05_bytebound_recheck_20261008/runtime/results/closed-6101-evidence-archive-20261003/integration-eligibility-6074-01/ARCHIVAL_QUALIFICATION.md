# Qualification for recovered #6074 integration-boundary evidence

This is a byte-preserving copy of the five-file package at
`runtime/results/integration-eligibility-6074-01/` in remote branch
`integration/explicit-stopped-observe-20261001`, observed at
`f797619abb89dacc9c5842edba63e81674bb8db5` on 2026-10-03. The package files
were copied without editing; their Git blob IDs match the source branch.

## Reproduction and scope

An isolated extraction of the source package passed all entries in
`SHA256SUMS` before and after running `review.py` under Python 3 and
`python -O`. Both runs reproduced the four stored boundary results: unsupported
predicate, reversed interval, Boolean measurement, and unsupported duration
were each classified `ROBUST_TRUE_SCOPED` where the expected outcome was
`UNKNOWN_OR_TYPED_REFUSAL`. The disposition remains
`HOLD_RUNTIME_INTEGRATION`. No original T0 corpus or GUI/model/action run was
rerun, and no runtime code is adopted by this archive.

The historical `review.py` has a limitation: when the candidate raises, it
converts the exception to a dictionary and then treats any dictionary as
eligible. None of these four reproduced probes raised, so their recorded
`ROBUST_TRUE_SCOPED` outcomes remain reproducible; however, this script is not a
general fail-closed exception auditor. Preserve the original report unchanged
and do not use it to support broader claims.

## Historical status

The source README says the integration branch was pending parent PR #6077; that
describes the state when the review was recorded. PR #6077 has since merged to
main as `4526e4b19b6addebca5b498a8047f25929d39846`. Issue #6074 remains open;
this archive records only its separate boundary review and does not change its
T0 result, authorize product integration, or delete the source branch.
