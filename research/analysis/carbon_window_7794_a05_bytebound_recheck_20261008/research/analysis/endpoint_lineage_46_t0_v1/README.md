# Issue #46 T0 — endpoint identity and uncertainty aggregation

Status is decided by one exact finite candidate run and one separate vertex
auditor; neither run has occurred at the time of this freeze. This method check
is synthetic and does not measure real clocks or agent latency.

## H/T/D/C/U

- **H:** shared endpoint identities preserve a joint feasible set and allow
  algebraic cancellation; independent middle measurements do not cancel.
  Missing/incompatible clocks remain nonnumeric, and overlapping intervals do
  not certify nominal winners.
- **T:** exact rational fixtures in `fixtures.json`: same-clock shared ID,
  distinct middle IDs, shared affine cross-clock map, incompatible epoch,
  missing endpoint, and nominally ranked near-tie with an opposite feasible
  ordering. The candidate reduces symbolic linear expressions; a separately
  authored auditor enumerates all box vertices and checks raw candidate output.
- **D:** scoped PASS only if joint bounds equal independent vertex projections,
  independent IDs retain the added feasible range, incompatible/missing cases
  HOLD, and the nominal winner remains unresolved with a feasible reverse-order
  witness. Any excluded feasible vertex, false winner, unauthorized endpoint
  cancellation, or numeric missing/incompatible case is FAIL.
- **C:** direct outer-endpoint bounds or the existing affine-clock treatment in
  #4363 may be sufficient; a separate lineage reducer might add no decision
  value. No matched policy/latency or live endpoint-source comparison is made.
- **U:** authored finite rational intervals are not calibrated clock
  uncertainty, covariance, semantic endpoint validity, application effects,
  latency, or #59/MAP01 evidence. No probability or safety inference.

## Reproduction

From repository root:

```sh
python3 research/analysis/endpoint_lineage_46_t0_v1/reducer.py
python3 research/analysis/endpoint_lineage_46_t0_v1/audit_independent.py
```

`FREEZE.json` and `SHA256SUMS` bind the source-main SHA, fixture and executable
sources. After the single candidate execution, its exact stdout is preserved in
`candidate_stdout.json`; the auditor reads that file and independently
reconstructs each disposition. The result and scope are in `RESULT.md`.
