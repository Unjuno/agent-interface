# T0 execution record

- Frozen scope: `PLAN.md`, `cases.json`; no changes after the single final candidate/audit invocation except this record/report and hashes.
- Command: `python research/analysis/interval_robustness_6074_t0_20261002/audit.py`
- Runtime: Python 3.12.10, Windows host; no GUI, model, or input.
- Candidate invocations: 1 (audit launches candidate once and oracle once).
- Auditor invocations: 1.
- Result: `METHOD_PASS_SCOPED`; zero audit errors; nine of nine case expectations matched; three mutation checks passed.
- Container preflight: Docker Desktop processes were present, but `docker --context desktop-linux version --format 'client={{.Client.Version}} server={{.Server.Version}}'` yielded no output; the one CLI attempt was interrupted. No container execution occurred.
- No retries or formal/live allocation consumption.
