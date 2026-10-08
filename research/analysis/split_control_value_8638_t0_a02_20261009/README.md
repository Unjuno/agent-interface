# Issue #8638 split-control value, T0 A02

This package is a fresh successor allocation to Issue #8638 A01. A01's candidate and auditor ran once and reported a method pass in memory, but its full 48-row raw table was not persisted. That artifact-custody STOP remains unchanged; A02 does not reuse or rerun either A01 program.

A02 freezes 13 synthetic cases: 12 supported profiles with 16 exhaustive state/signal/delivery/uptake rows each, plus one out-of-model profile that must remain unscored. The separate raw-only auditor reconstructs all 192 supported rows, exact rational expected losses, the acquisition-versus-uptake ranking, and the hard-gate invariants. The finite fixture tests whether a single-controller VOI-C or acquisition-only information-minus-cost proxy can rank a high-quality but rarely consumed signal above one with lower quality and reliable uptake, while actual split-control net value reverses the ranking.

Formal execution is pending the frozen preregistration. The evidence files `raw/candidate_raw.json` and `raw/audit.json` are absent until the one candidate run and one independent audit complete. Read [PROTOCOL.md](PROTOCOL.md), [FREEZE.json](FREEZE.json), and [CONSTRUCTION.md](CONSTRUCTION.md) for the frozen rules and pre-run checks.

No model, GUI, user, application, network service, or runtime route is part of this experiment. It cannot establish deployed planner uptake, real observation value, task effects, safety, or product benefit. Authority is always `NONE`; mandatory validity, freshness, authority, release, and independent-effect gates remain outside the value ledger.
