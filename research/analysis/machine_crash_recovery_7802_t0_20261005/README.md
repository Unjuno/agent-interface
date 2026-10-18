# Machine-crash recovery boundary — Issue #7802 T0

**Disposition: `PASS_METHOD_SCOPED_T0_ONLY`.** A finite, authored crash-image model exposed three machine-only state tuples; the independent raw-only auditor reconstructed all 31 rows and rejected all four mutations. No physical host crash, VM, SQLite VFS, container, or live effect was tested.

Start with [`REPORT.md`](REPORT.md). The exact source and pre-run hashes are in [`FREEZE.json`](FREEZE.json); commands, environment, raw hashes and invocation counts are in [`RUN.json`](RUN.json). The model limitation and the conditional VM T1 gate remain binding.
