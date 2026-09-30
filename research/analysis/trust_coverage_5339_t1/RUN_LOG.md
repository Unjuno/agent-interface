# Run log

- Freeze: main `57b56de2831204885c55375737580e5d82d3ab98`.
- First candidate command: `python3 -I research/analysis/trust_coverage_5339_t1/candidate.py`; exit 0; 11 traces; raw SHA-256 `fa1caf6add6ba80c7396da46820de45fffe7bbe14fbc8fbfda9b16fec0d4bd3d`.
- First auditor command: `python3 -I research/analysis/trust_coverage_5339_t1/audit.py`; exit 1. First output is retained as `audit_first_stop.json`; candidate raw was not changed.
- Corrected raw-only auditor command: same command; exit 0; 11 rows checked; 11/11 contract labels match; 3 unsafe any-singleton false admissions surfaced.
- Syntax gate: `python3 -m py_compile .../candidate.py .../audit.py`; exit 0.
- Local CI: `pytest -q research/analysis/trust_coverage_5339_t1/test_t1.py`; 3 passed.
- Whitespace gate: `git diff --check`; exit 0.
- Container/Obstac: no experiment container launched. GitHub #5085 records Docker inventory unobservable and a competing client still alive; no exact released slot. No Obstac command or MCP tool is exposed in this session. These are environment/resource constraints, not a research result.
- No external action, GUI, model, GPU, network, or hidden state accessed by the candidate/auditor.
