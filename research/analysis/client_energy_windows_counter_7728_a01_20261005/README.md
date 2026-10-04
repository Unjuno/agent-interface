# Issue #7728 Windows energy-counter cross-check

This is the Windows-host-specific A01 follow-up. It does not change the macOS sensor result or authorize a route pilot.

- `PREREGISTRATION.md` — scope, decision rule, limitations, and stop rule.
- `FREEZE.json`, `SHA256SUMS` — frozen base and source/SDK hashes.
- `emi_probe.cs`, `run_preflight.ps1` — one-shot read-only EMI/counter bracket.
- `raw-preflight.json` — sanitized raw output from the single candidate invocation.
- `audit_preflight.py`, `audit.json` — independent raw-output audit and mutation controls.
- `OUTPUT_SHA256SUMS` — post-run hashes for retained raw and audit output.
- `REPORT.md` — result and bounded interpretation.
- `CONSTRUCTION.md`, `test_audit_preflight.py` — pre-freeze source and synthetic checks.
