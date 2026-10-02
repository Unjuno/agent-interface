# r133 cross-domain coverage identifiability

Retrospective, source-pinned audit for Issue #59’s instruction to transfer coverage semantics to a non-DOOM domain. This is intentionally distinct from PR #6111’s OpenTTD clock-join audit: it places the retained DOOM program-envelope metric, explicit physical-edge requirement, independent useful-effect endpoint, and denominator on one common eligibility contract across both domains.

The expected result is a qualified **HOLD**, not a numeric time-coverage value. Source traces remain on main and are fetched by the exact commit recorded in `FREEZE.json`; `download_inputs.py` verifies each SHA-256 before analysis.

1. `python3 download_inputs.py`
2. `python3 -m unittest -v test_candidate test_independent_audit`
3. After verifying `FREEZE.json` and source hashes, `python3 run_candidate.py` once.
4. Only after candidate exit 0, `python3 independent_audit.py` once.

No game/model/GUI/input, X server, Docker, WSL, or GPU is invoked. See `PLAN.md` for H/T/D/C/U and the scope boundary.
