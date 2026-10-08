# Issue #5156 — Allocation 07 source and STOP archive

This allocation ended at the pre-candidate coordination gate. The retained
record is a resource/provenance STOP, not an experimental PASS or FAIL.

- Frozen scope: explicit per-key owner-thread `KeyRelease`/`XSync` bracket
  timing; see `PLAN.md`.
- Observed gate: four nonterminal `Created` containers had no resolved owner or
  release record in the shared queue. The record required leaving all unrelated
  containers untouched.
- Disposition: `STOP_RESOURCE_COORDINATION_BEFORE_CANDIDATE`; candidate 0,
  independent auditor 0, container starts 0, image inspections 0,
  `scientific_result=NOT_EVALUATED`.
- The original `STOP.json`, read-only `START_GATE_INVENTORY.json`, and source
  package are preserved unchanged. No retry or successor authorization is
  implied.
- Local CPython 3.14.5 synthetic/launch-construction tests: 23/23 pass. These
  tests do not invoke the frozen runner, inspect or start containers, or run an
  auditor against formal raw.

See [`ARCHIVAL_QUALIFICATION.md`](ARCHIVAL_QUALIFICATION.md) for exact source
tip and local validation limits.
