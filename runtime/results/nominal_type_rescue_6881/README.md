# Rescue of #6881 nominal type-boundary evidence

Source: `8e40dd8170c7ec57ad0738e074a99b9674d737d4`, original PR #6881,
Issue #6875. This delivery preserves all 43 original public Git blobs under
`runtime/results/kernel-type-boundary-01a0ff2d-eb8e/`, without normalization or
replacement of the retained first failures, original audits, or publication history.

`python -B runtime/results/nominal_type_rescue_6881/test_archive.py -v`
checks all 42 manifest entries, all 18 disclosed CRLF inverses, five original
source Git-blob pins, and both complete 28-row raw projections. It invokes the
original independent raw-only auditor on fresh temporary outputs, requires exact
equality with both v2 receipts, and verifies all ten candidate corruption controls.
The path-sanitized first-failure inverse is a public derivative, not recovery of
private traceback paths. Earlier publication errors remain historical evidence.

The baseline accepted six shaped malformed records; the isolated candidate
accepted zero. Both accepted seven typed records. These are finite synthetic
API fixtures, not physical effects or independent reliability trials. Historical
baseline exit 1 remains retained. Fresh isolated candidate unit tests are ordinary
engineering checks, not a new formal allocation. Shared `runtime/kernel` is not
changed: production promotion and composition belong to separate PR #6923.

This rescue uses local read-only audit/construction CI. It does not rerun either
primary probe, allocate a container/VM, make backend input, or claim current-main
nominal protection, hostile-subclass safety, concurrent safety, live authority,
latency or task-effect benefit. Container/native execution would require its own
appropriate gate; no other worker's allocation is reused.
