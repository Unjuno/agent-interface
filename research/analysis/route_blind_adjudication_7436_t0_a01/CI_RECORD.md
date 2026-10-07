# A01 checks and formal execution record

- Construction suite: 5/5 PASS after correcting a no-op test mutation.
- `py_compile` for presenter, candidate, auditor, tests: PASS.
- CRLF-aware `git diff --check`: PASS.
- Container eligibility check: STOP; OrbStack containerd image listing failed before any container invocation. Host-only fallback was preregistered.
- Candidate CLI, once: exit 1 (`ModuleNotFoundError: No module named 'presenter'` under `python3 -I`). Exact stdout and exit status are retained in `results/`.
- Auditor: not invoked because candidate exit was nonzero.
- Formal retries: 0.

This failure shows that the construction tests did not cover the actual isolated CLI entrypoint. It does not evaluate route-blinding behavior.
