# Corrected Needle covariate audit (#3899)

This audit-only successor fixes the prior auditor's invalid IID/shift equality condition. The shifted CORRECT generator intentionally changes dx, dy, velocity, and confidence; each suite is instead checked against its own seed-derived expected six-vectors. Original pilot-06 remains `FAIL_NEAR_BOUNDARY_SHIFT`.

See [PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U, input identity, decision gates and limitations. `audit.py` reads only the retained `FORMAL_RESULT.json`; it imports no training runner. One formal local Docker audit is allowed after the freeze is complete. No model execution, training, GPU, network, or retries.

The immutable formal STOP and scientific FAIL are summarized in [REPORT.md](REPORT.md); `FREEZE.json` records source/input/environment identities. Do not rerun this allocation.
