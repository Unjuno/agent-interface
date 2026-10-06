# Provenance-checked defeasible obligations — T0 A01

This is a finite synthetic method experiment for Issue #7817. It evaluates
source-bound rules for one abstract action/context; its result is explanatory
and never dispatches an action or grants authority.

The candidate resolves only opposite obligations backed by an authenticated,
current, in-scope, acyclic explicit priority path. Missing source coverage,
duplicate version identities, invalid priority edges, cycles, strict-rule
attacks, and unresolved/incomparable conflicts fail closed as `UNKNOWN_STOP`.
The independent audit uses an explicit expected-outcome ledger and separately
checks proof coverage, authority boundaries, and five hostile mutations.

Execution provenance and limits are in `FREEZE.json`, `RUN.json`, and
`REPORT.md`; raw stdout/stderr are retained under `raw/`.
