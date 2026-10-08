# Issue #8421 — system-carbon rebound T0

This directory contains the frozen synthetic accounting-method experiment described in [`PROTOCOL.md`](PROTOCOL.md). T0 tests ledger arithmetic and boundary/denominator integrity only; it contains no empirical energy or carbon observation and makes no environmental or GUI-agent claim.

- `SOURCE.json`: exact synthetic opportunities, activity/component rows, grid-factor sensitivity bounds, and separate embodied allocation.
- `candidate.py`: materializes the raw ledger and its claimed summaries.
- `audit.py`: independently validates source bytes and row identity, then recomputes both estimands without importing candidate code.
- `test_contract.py`: pre-freeze construction tests and hostile mutation controls.
- `formal_01/`: one-shot candidate raw, independent audit, and execution receipt (written only after freeze).

See [`REPORT.md`](REPORT.md) for the formal disposition after the frozen one-shot run.
