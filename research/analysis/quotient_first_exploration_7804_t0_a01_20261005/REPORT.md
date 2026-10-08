# Issue #7804 T0 A01 — first outcome

## Disposition

`STOP_INFRA_AUDITOR_LAUNCH`. The candidate process ran once, exited 0, and emitted a raw JSON artifact. The independent auditor launch was attempted once but exited 125 before its Python process started. Docker rejected a relative bind source path for the candidate output (`research/analysis/quotient_first_exploration_7804_t0_a01_20261005/results/a01/candidate.raw.json`); the auditor requires an absolute host path. Retries: 0. The frozen allocation is not rerun or repaired.

The candidate raw file reports 312 named states, 166 typed quotient classes, 1,484 generated full-search transitions, and 803 quotient-first transitions. These remain candidate-reported observations only. No independent formal reconstruction or counterexample-lifting result was produced, so the Issue's PASS/FAIL gate is unresolved. No scientific outcome is inferred from the launch failure.

## Provenance and scope

- Issue: https://github.com/Unjuno/agent-interface/issues/7804
- Allocation: `APPLICATION-QUOTIENT-FIRST-7804-T0-A01-20261005-01`
- Base main: `aeed696ff756d68497faed39b92e3546cb144972`; freeze commit: `1eb39150ed31bbe507321c64cb6e2fd209fdfcb2`.
- Candidate exit: 0; auditor launch exit: 125; auditor Python executions: 0; retries: 0.
- Candidate stdout/stderr, raw output, auditor stdout/stderr and exit receipt are hash-listed in `results/a01/SHA256SUMS`. The auditor stderr retains Docker's exact mount error.
- Construction tests passed 7/7 before freeze; role-specific read-only mount probes passed. These do not substitute for the missing formal auditor.
- The predecessor #6257 package's source hashes match its manifest. Its old raw SHA256SUMS entries do not match the tracked raw JSON bytes. This allocation preserved the files unchanged and pinned the actual historical bytes by Git blob identity and recomputed SHA-256; see `results/preflight/predecessor_integrity.json`.

The experiment concerns an authored finite model only. Even a successful method audit would not establish production memory savings, wall-clock speedup, runtime authority, real-worker interchangeability, liveness, GUI behavior, or deployed safety.
