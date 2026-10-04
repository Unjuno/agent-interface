# Issue #7728 Windows energy-counter A02

A02 extends the Windows-host-specific A01 single-sample EMI/counter identity check with six repeated raw samples and an ambient CPU-utilization trace. It does not run a controlled load or task.

- `PREREGISTRATION.md` — H/T/D/C/U and no-retry stop rule.
- `FREEZE.json`, `SHA256SUMS` — exact main base, source hashes, and SDK-header hash.
- `emi_probe.cs`, `run_a02.ps1` — reused read-only EMI probe and one-shot six-sample counter capture.
- `raw-a02.json`, `audit-a02.json` — one candidate outcome and independent audit.
- `OUTPUT_SHA256SUMS` — post-run output hashes.
- `audit_a02.py`, `test_audit_a02.py`, `CONSTRUCTION.md` — raw auditor and pre-freeze synthetic checks.
- `REPORT.md` — result, provenance, and limits.
