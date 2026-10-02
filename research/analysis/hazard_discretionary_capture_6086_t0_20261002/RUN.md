# T0 execution record

- Frozen input: `freeze.json` and `PLAN.md` were written before the first formal calculation.
- Command: `python research/analysis/hazard_discretionary_capture_6086_t0_20261002/audit.py`
- Runtime: Python 3.12.10, local Windows host.
- Invocations: auditor once; it launched candidate once and integer half-tick oracle once. No retry.
- First disposition: `FAIL_METHOD`; width-1/2 improvement gate missed. Auditor additionally reported `candidate_oracle_mismatch` because it compared unlike row schemas; separate oracle rows were not retained.
- Issue-T0 coverage audit: partial only. Imperfect exposure, false-positive accounting, worst-onset/max-gap, explicit no-cue row, scored-label leakage rejection, zero/unknown hazard, and all-budget-mandatory control were omitted.
- Docker: host's Docker Desktop `desktop-linux` server probe had hung immediately beforehand; no container run or container PASS is claimed.
- No model, GUI, input, or live/formal allocation.
