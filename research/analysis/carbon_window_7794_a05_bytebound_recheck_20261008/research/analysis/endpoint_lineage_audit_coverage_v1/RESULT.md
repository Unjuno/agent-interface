# Result — endpoint-lineage audit coverage successor

Disposition: **`PASS_ENDPOINT_LINEAGE_AUDIT_COVERAGE_SCOPED`**.

This is an additive audit-quality result for Issue #46 / PR #5755. It does not
revise the predecessor's frozen candidate output or scoped scientific result.

## Freeze and execution

- Allocation: `ENDPOINT-LINEAGE-AUDIT-COVERAGE-20261001-01`.
- Frozen predecessor: commit `68a4a983118fbbfaecf875c44fe04fadff3b4bd9`,
  source main `0afd3e33b9da5e8ed4c8307609fec3264d4b93f2`.
- Frozen input hashes are in `FREEZE.json`; the final successor source hashes
  were checked with `SHA256SUMS` before the formal run.
- Command: `python3 endpoint_audit_coverage_probe.py` with Python 3.14.5,
  standard library only; exit 0.
- v1 control: unchanged output and two isolated corruptions each returned exit
  0 / `PASS_ENDPOINT_LINEAGE_T0_SCOPED`: altered first `naive_sum` to
  `[-900,900]`, then altered an ordered first segment interval to `[-500,500]`.
  This confirms the preregistered coverage gap.
- v2 control: unchanged output returned exit 0 /
  `PASS_ENDPOINT_LINEAGE_T0_ALL_FIELDS_SCOPED`.
- v2 negative controls: each of the 38 numeric-string values across joint
  intervals, `naive_sum`, segment intervals, symbolic expressions, near-tie
  intervals and the reversal witness was independently increased by 1 in its
  own copy. All 38 returned exit 1 with the expected `AssertionError`; none
  were accepted. The complete path/exit/assertion evidence is retained in
  `result.json`.
- The candidate reducer was not run. No container, model, GUI, clock capture,
  game, network-dependent experiment input, or shared resource was used.

## Interpretation and limits

The v1 `mismatches: 0` label certified only its implemented assertions, not all
fields displayed in candidate stdout. The successor demonstrates this by
changing the omitted fields while preserving the v1 PASS. The v2 auditor
independently reconstructs each segment projection, independent sum, joint
projection, status, symbolic expression, and near-tie result for these authored
fixtures, then rejects isolated mutations to every numeric-string output
field.

The result is limited to fixed synthetic inputs and output schema. It is not a
clock-calibration result or evidence about real timestamps, endpoint
provenance, live latency, MAP01 control, or system safety. The predecessor PASS
and artifacts remain untouched.

