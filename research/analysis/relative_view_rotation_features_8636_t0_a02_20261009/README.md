# Issue #8636 T0 A02 — corrected focal-shift audit taxonomy

A fresh finite synthetic validation allocation for the rotation-feature idea. It preserves A01's `HOLD_UNCERTAIN` and first audit failure, while correcting only the focal-shift YIELD classification and using a disjoint seed set. See `PROTOCOL.md` for exact H/T/D/C/U and changed conditions.

- `FREEZE.json`: current-main base, A01 lineage, frozen inputs/source hashes, and one-pass run ledger.
- `candidate.py`, `runner.py`, `auditor.py`: fixed candidate and renderer plus independent corrected raw-only auditor.
- `test_construction.py`: construction regression tests, including the retained A01 focal-shift counterexample.
- `results/a02-outcome/`: one candidate output and one independent audit, including raw PPM frames and exact stdout/exit records.
- `REPORT.md`, `FORMAL_RUN.md`, `SHA256SUMS.txt`: result, commands, custody, and integrity manifest.

This is CPU-only synthetic evidence. It does not support live GUI/game, task-effect, physical release, user, runtime, product, or safety claims.
