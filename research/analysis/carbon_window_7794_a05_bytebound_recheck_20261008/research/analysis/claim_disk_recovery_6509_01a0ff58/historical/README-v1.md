# Actual disk-prefix recovery after process exit — #6509

Decision: **PASS_PROCESS_EXIT_BOUNDARY_SCOPED** for nine frozen, authored native Windows construction cases. This is a new ordinary construction boundary after the original logical T0; neither historical allocation was rerun.

See [report](REPORT.md), [prospective plan](PLAN.md), [source/case freeze](FREEZE.json), [run commands and UTC exits](RUN.json), [first raw](results/boundary-01/raw.json) and [separate retained-file audit](results/audit-01.json). SHA256SUMS pins the published files. The original [T0](../claim_scoped_partial_verdict_6509_t0_20261002/REPORT.md) remains unchanged.

From repository root, ordinary tests:
```text
python -m unittest discover -s research/analysis/claim_disk_recovery_6509_01a0ff58 -p test_recovery.py -v
```

To inspect retained evidence without rewriting it:
```text
python research/analysis/claim_disk_recovery_6509_01a0ff58/audit.py research/analysis/claim_disk_recovery_6509_01a0ff58/results/boundary-01 NEW-AUDIT.json
```

The audit refuses an existing output. A fresh ordinary construction matrix, if justified, needs a distinct output, identity, freeze and retained first result. Do not overwrite or rerun this boundary-01 to improve its outcome.

All labels describe synthetic check receipts. The package is research-only and neither imports into runtime nor grants GUI/input authority. Process-exit visibility is not power-loss durability, concurrent publication, exactly-once consumer effects or a performance claim.
