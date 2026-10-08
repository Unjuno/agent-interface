# Excluded construction notes

- Exploratory startup: observer omitted `XAUTHORITY`; stopped before usable acquisition. Scientific formal cases consumed: 0.
- Corrected nine-case construction: expected one-repetition matrix observed.
- Auditor construction v0: `policy_relabel` produced an `AttributeError`; old auditor retained at `construction/audit_v0_crash.py` and incident retained in `construction/AUDITOR_CONSTRUCTION_FAILURE.json`.
- Auditor construction v1: 11/12 mutations rejected; `schedule_relabel` was not detected because raw event ordering was not checked. Old auditor retained at `construction/audit_v1_11of12.py` and incident retained in `construction/AUDITOR_CONSTRUCTION_FAILURE_V1.json`.
- Final auditor: nine cases, 327 checks, errors=[], 12/12 mutations rejected; six unit methods pass. This was frozen and publicly read back before formal case 0.
- A later read-only local audit invocation used obsolete command-line flags and exited 2 before the correct read-only invocation; no source, construction row or formal result changed.
