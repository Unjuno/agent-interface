# Issue #7748 duplicate-ID input boundary A02

A02 is a fresh additive allocation for the duplicate-job-identity defect in the existing #7748 diagnostic. A01's `STOP_AUDITOR_EXIT_MISMATCH` remains preserved as a separate result. A02 carries forward the same three frozen fixtures and identity-boundary method; its only code change is the auditor CLI exit mapping, with raw schema versioned to A02. Read `PROTOCOL.md` and `FREEZE.json` before its one-shot candidate/auditor pair; see `REPORT.md` and `RUN.json` for the result.

This is finite synthetic method evidence only. It does not establish real scheduler behavior, runtime or task effects, safety, or physical release.
