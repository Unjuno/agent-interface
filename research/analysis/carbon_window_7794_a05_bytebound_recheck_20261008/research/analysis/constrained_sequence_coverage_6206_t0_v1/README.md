# Constrained sequence coverage T0 package

- `PLAN.md`: frozen H/T/D/C/U and decision gates.
- `FREEZE.json`: source identities and pre-run allocation record.
- `candidate.py`, `audit.py`, `fixture.json`, `test_candidate.py`: frozen source and construction tests.
- `candidate.json`, `audit.json`: one-shot formal output and independent raw-only audit; do not overwrite or rerun.
- `REPORT.md`, `RUN.json`, `SHA256SUMS`: scoped interpretation, execution receipt, and integrity manifest.

The result is synthetic method evidence only. See `REPORT.md` for denominators, limitations, and the preserved pre-run construction correction on Issue #6206.
