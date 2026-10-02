# A04 run record — raw computation completed; auditor invalid

**Disposition:** `INCONCLUSIVE_AUDITOR_FAILURE`; no formal parity PASS.
Candidate invocation: 1; both arms exited 0. Auditor invocation: 1; exit 1.
Retries: 0.

The R and Python arms each produced six raw rows. The independent auditor
crashed at its first scale-mismatch diagnostic because it formatted a missing
R `case_id` field (`KeyError: 'case_id'`). The traceback is retained in
`output/audit.txt`. It therefore did not complete its predeclared comparison.
No auditor rerun was made.

Post-hoc inspection of the preserved raw artifacts (not a replacement for the
failed auditor) found: all six thresholds match exactly; upper candidate-index
sets match for all six; sensitive-index sets match for all six after
normalizing JSON scalar versus one-element-array representation. Across the
valid base-fit rows only, maximum relative scale discrepancy is
`1.4245611e-4`, maximum absolute shape discrepancy is `1.4604392e-4`, and
maximum absolute CI-endpoint discrepancy is `2.3821770e-4`. The frozen A04
shape/scale tolerances were tighter (`1e-5`), so at least the first baseline
fit misses that frozen numerical gate.

The post-hoc sequential-fit rows are not valid parity evidence: inspection
found the Python reporting harness recomputed each restored candidate from
the original base sample instead of accumulating previously restored points.
The production Python `tailid_sensitive_upper` arm itself ran once and its
reported sensitive sets match the R arm, but the per-step fit trace cannot be
compared. The auditor defect and Python trace defect are both preserved; A04
was not patched or rerun. This supports a new additive successor only.

This outcome is a measurement/harness failure plus descriptive baseline
numerical drift, not evidence of estimator superiority and not formal #6576 T0.
See `FREEZE.md`, `SHA256SUMS`, raw inputs, R/Python outputs, and logs.
