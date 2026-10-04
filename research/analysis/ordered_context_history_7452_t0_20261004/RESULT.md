# Formal result — Issue #7452 T0

- Allocation: `ORDERED-CONTEXT-HISTORY-7452-T0-20261004-01`
- Outcome: **PASS_METHOD_SCOPED**.
- Candidate: one invocation, exit 0; independent auditor: one invocation, exit 0; retries: 0.
- Run time: 2026-10-04, approximately 04:55 UTC (the local command returned before the 04:56:05 UTC receipt/hash snapshot).
- Frozen base: `0db425b379f9438bf6b13c95dce1b763750b06d5`.
- Runtime: Ubuntu WSL2, Linux `6.18.40.1-microsoft-standard-WSL2`, Python 3.12.3, x86_64. The allocation ran on native WSL2, not in WSLc/Docker. WSLc `container list --all` had an already-live no-output call; it was not restarted, and the process was left untouched. This result makes no container-runtime portability claim.
- Candidate command: `wsl.exe -d Ubuntu -- python3 <package>/candidate.py <package>/results/candidate`.
- Auditor command: `wsl.exe -d Ubuntu -- python3 <package>/auditor.py <package>/results/candidate/candidate.json <package>/results/audit.json`.
- No network, model, GUI, input, GPU or external service was used.

## Reconstructed outcome

- Legal pair-history denominator: 10. `RELEASE` requires prior `ACT`; no release repetition; no ACT after release.
- Mixed context-pair × ordered-event suite: 40/40 expected cells, exact; exhaustive full-context-pair denominator: 80 rows.
- Separate context-pair and event-pair certificates plus fixed-context padding: 40 rows, equal budget.
- Seeded joint `focus=1 ∧ surface=1 ∧ REVOKE→ACT` mutant: mixed detects; separate equal-budget baseline misses.
- Factor-only and order-only controls: both detected by the separate baseline. The order-invariant control is detected by both suites.
- Independent raw audit: `errors=[]`, `coverage_exact=true`.
- Construction suite on frozen files: 5/5 PASS; `py_compile` PASS. Controls rejected context-stratum collapse, impossible release-before-action, and missing target-order cells. The auditor ignored candidate-provided expected-denominator metadata and independently reconstructed its denominator. The earlier 4/5 duplicate-row construction failure remains disclosed in `CONSTRUCTION_HISTORY.md`.

## Immutable raw outputs and source identity

- Candidate raw JSON: `results/candidate/candidate.json`, SHA-256 `7469965d8c43ed22e37d3bdc443eb4560da5457de016c62ce45e0c65622fab4f`.
- Independent audit JSON: `results/audit.json`, SHA-256 `d2f6ca75699e3883481bd5378729b525168f66e80dbe9b2110937deb562857cc`.
- Frozen source hashes are listed in `FREEZE.md`; candidate, auditor, test and fixture have not changed since formal execution.

## Limits

One deliberately small authored model and seeded counterexample show that these two particular separate summaries can miss this particular context-conditioned order fault at the same row budget. This does not show that real GUI histories have these semantics, that ordered t-way coverage is generally better, that a natural fault exists, or that any GUI/runtime is safe or reliable. Freshness is not crossed with the event tuple; higher-order and continuous interactions remain outside the tested strength. The result neither modifies nor upgrades #6206 or #6262.
