# Issue #8636 T0 A02 — corrected focal-shift audit allocation

This fresh allocation preserves A01's `HOLD_UNCERTAIN` and uses a disjoint seed set to test the rotation-feature fixture under a corrected focal-shift audit taxonomy. The formal auditor stopped before summary generation; disposition remains `HOLD_UNCERTAIN`.

- `PROTOCOL.md`, `FREEZE.json`, `FREEZE_AMENDMENT.md`: pre-registered delta, base and source hashes.
- `candidate.py`, `runner.py`, `auditor.py`, `test_construction.py`: source and regression checks.
- `results/a02-first-outcome.tar.gz`: byte-verified first candidate output.
- `results/candidate.*`, `results/auditor.*`: exact stdout, timestamps, and exit codes.
- `FORMAL_FAILURE.md`, `FORMAL_RUN.md`, `REPORT.md`: first outcome, custody, and limits.
- `SHA256SUMS.txt`: package integrity manifest.

Do not rerun this consumed allocation. A01 remains separate and unchanged. No live GUI/game or product claim is made.
