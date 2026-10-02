# Issue #6645 — counterexample-qualified skill guard refinement

Finite synthetic T0 only. The package compares unchanged guard, fallback-only,
exact-state blacklist, candidate predicate refinement, and an oracle-minimal
diagnostic. Candidate code consumes independently verified controls and replay
classifications but does not read hidden oracle truth. The auditor independently
reconstructs decisions and tests hidden-family observation aliases.

Current work is construction evidence, not formal T0: 13 construction/mutation
tests pass on host CPython; the source candidate and separate auditor have not
run in WSLc. A pre-allocation source freeze is recorded in `FREEZE.json` against
main `007503a7b461848539dda5ba5a795cbfdc13b9db`; it is not an assignment or
authorization. Formal candidate/auditor/retries are 0/0/0. See
`RESOURCE_HOLD.md` and `RUN_RECORD.json` for the exact start gate and disposition.

No live GUI, task input, model, user, external effect, product safety, or
performance claim is present. T0 only tests whether a frozen finite method
fails closed under declared controls and an explicit hidden-family alias.
