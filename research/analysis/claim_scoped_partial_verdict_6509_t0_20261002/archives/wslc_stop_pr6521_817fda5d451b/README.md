# Claim-scoped partial verdicts — Issue #6509 T0

This additive package tests the finite protocol boundary only. It does not test GUI behavior, real deadlines, verifier quality, or authorization.

- `PREREGISTRATION.md` — H/T/D/C/U, fixture contract, and scope.
- `fixture.json` — frozen adversarial and control traces.
- `candidate.py` — three policy implementations over the same traces.
- `auditor.py` — raw-only independent reconstruction; imports no candidate module.
- `test_protocol.py` — construction and corruption tests.
- `RUN_PROTOCOL.md` — one-shot WSLc protocol and no-retry gates.

No formal result is claimed until a frozen WSLc construction rung and candidate/audit sequence are completed and raw outputs retained.
