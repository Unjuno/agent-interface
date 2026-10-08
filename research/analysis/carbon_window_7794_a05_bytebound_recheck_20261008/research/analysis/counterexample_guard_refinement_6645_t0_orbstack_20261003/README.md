# Issue #6645 — counterexample-qualified guard refinement T0

This additive package tests the finite, no-GUI T0 hypothesis in `PROTOCOL.md`.
It is distinct from #4260's guard-hit/deoptimization lifecycle and #5504's
verifier-predicate CEGAR result: the unit under test here is a reusable skill's
applicability guard after an independently replayed concrete miss, including
coverage-envelope abstention and sibling-specialization invalidation.

The package contains the preregistered fixture, candidate, separate raw-only
auditor, and corruption tests. `FREEZE.json` binds the exact source and cached
container image. Formal results, process records, stdout/stderr, and hashes are
retained under `results/formal_01/`; the executed disposition and limits are in
`REPORT.md`.

No runtime integration, GUI/model behavior, real skill, user data, task input,
external effect, or product/safety claim is established by this fixture.
