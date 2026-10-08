# Issue #5686 T0 — synthetic surrogate-gate construction

This package executes the minimum analytical/synthetic rung proposed by [Issue #5686](https://github.com/Unjuno/agent-interface/issues/5686). The experiment tests whether an interface metric gate avoids finite false promotions; it does not validate a real interface metric.

- `PREREGISTRATION.md` — H/T/D/C/U and frozen decision contract.
- `fixtures.json` — 24 paired potential-outcome attempts in five authored worlds and two strata.
- `candidate.py` — candidate evaluator, emitting every input attempt and one decision summary per world.
- `audit.py` — independent raw-only audit of candidate JSONL against the frozen fixture; it does not import candidate code.
- `test_gate.py` — local tests, including dropped-attempt and altered-stratum corruption cases.
- `.github/workflows/issue-5686-surrogate-gate-t0.yml` — one-shot branch-creation workflow with candidate and raw-only auditor in separate digest-pinned Docker containers on isolated GitHub-hosted runners.
- `raw/development/` — host-native development iteration only; not the formal Docker result.
- `FREEZE.json`, `raw/formal/`, and `REPORT.md` are to be added before/after the exact one-shot dispatch as source freeze and formal evidence.

The required audit disposition is scoped: positive concordance in two authored strata remains `PREDICTIVE_VALIDITY_UNESTABLISHED`. No synthetic outcome grants runtime authority or a product claim.
