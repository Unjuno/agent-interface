# Constrained interaction testing — Issue #5330 T0

The first Docker allocation stopped before runner import because the repository package root was missing; it remains recorded as `STOP_RUNNER_IMPORT_ROOT` in `results/formal-01/`. A distinct, separately frozen allocation corrected the mount root and completed in Docker. Its finite synthetic generator-sensitivity result is `PASS_DESIGN_SENSITIVITY_ONLY`; the separate raw-only auditor returned `PASS_AUDIT` with no errors.

The pairwise design covered 24/24 binary value-pairs and detected its deliberately planted freshness×lease oracle in 6 rows, while OFAT used 5 rows and missed it. The three-way design covered 32/32 triples and detected its planted freshness×responsibility×delivery oracle in 8 rows versus 16 exhaustive assignments. Exact rows, hashes, and audit values are retained under `results/formal-02/`.

This only verifies finite design sensitivity to planted synthetic conjunctions. It does not establish realistic factor independence, useful hazard-detection rates, Agent Interface runtime safety, or superiority on authentic repository failures. See [`README.md`](README.md) for H/T/D/C/U, `FREEZE.json` and `FREEZE_V2.json` for allocations, and [`results/formal-02/RESULT.md`](results/formal-02/RESULT.md) for provenance and the actual nested first-write output path.
