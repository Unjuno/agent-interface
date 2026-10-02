# Isolated verifier challenge lane — Issue #6477

Successor to #6461/T0b and #6179. T0b's pre-formal STOP and construction run remain unchanged. This fresh allocation will test the same synthetic broker-boundary hypothesis with one-shot construction, candidate, and raw-only audit rungs.

- `PREREGISTRATION.md` — H/T/D/C/U and scope.
- `RUN_PROTOCOL.md` — WSLc isolation, current-main/owner gates, and no-retry sequence.
- `candidate.py` — finite synthetic challenge lane and actual attack-envelope submissions.
- `auditor.py` — independent raw-only reconstruction; imports no candidate code.
- `test_protocol.py` — host construction/mutation tests.
- `build_check.py` — WSLc construction gate that verifies the exact 1 GiB cgroup ceiling before running the suite.

No production verifier, model, GUI, GPU, user data, or external effects are in scope. No result is claimed until WSLc raw candidate output and independent audit are retained.
