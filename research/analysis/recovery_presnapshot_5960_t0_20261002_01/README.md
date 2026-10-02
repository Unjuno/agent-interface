# Bounded pre-recovery capture — Issue #5960 T0

This deterministic finite-state construction probes whether a source-bound, minimal volatile snapshot can preserve a planted distinction that recovery erases, while safety/stop, privacy, deadline, receipt and freshness gates remain dominant. It does not use or model a real application, user data, GUI, input device, model or GPU.

Run `python -m unittest -v test_t0.py`, then inspect `FREEZE.json`, then run `python run_candidate.py` exactly once and `python independent_audit.py` exactly once. Do not rerun the formal candidate/auditor allocation; construction tests are separate. `RUN.json` and SHA256SUMS retain exact outcomes and scope.
