# Machine-crash recovery boundary — Issue #7802 T0

**Post-publication correction:** the original `PASS_METHOD_SCOPED_T0_ONLY` acceptance is superseded by [`ERRATUM-20261122.md`](ERRATUM-20261122.md): all four formal output mutations were not submitted to the audit function, so the frozen T0 decision rule is not established. The retained evidence still supports 31/31 row reconstruction and three machine-only tuples in the authored model. No allocation was rerun.

**Original frozen-run record (preserved):** the candidate/auditor ran once; the original output reported 31 rows and four mutation flags. Those bytes remain unchanged, with their mutation-control limitation documented in the erratum. No physical host crash, VM, SQLite VFS, container, or live effect was tested.

Start with [`REPORT.md`](REPORT.md). The exact source and pre-run hashes are in [`FREEZE.json`](FREEZE.json); commands, environment, raw hashes and invocation counts are in [`RUN.json`](RUN.json). The model limitation and the conditional VM T1 gate remain binding.
