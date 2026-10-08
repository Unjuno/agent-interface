# First outcome — Issue #59 occupancy ledger T0

**Disposition: `PASS_METHOD_SCOPED` (exploratory host-only construction).**

One candidate invocation emitted the deterministic two-key ledger; a separate raw-only auditor independently reconstructed it and rejected all five corruption controls. `SPACE` was bounded to 32–50 ns and `W` to 70–90 ns. The two key intervals remain separate; the report does not merge them into a continuous-control or task-effect metric.

The host test suite passed 6/6. Candidate and auditor both exited 0; retries=0. Raw SHA-256: `890d8c5ad8eca2c6d5583007029bb6e71f7a87df725945fa7bf2ce8f45b04161`. Auditor SHA-256: `f0377a4eb1136c48fdf59f62c589edef0c2830a0002e38f09599d8e9106d5d2b`.

## Interpretation

The construction demonstrates that the declared request/sync brackets and sampled down/up/empty witnesses are sufficient for this finite fixture to compute conservative per-key bounds and fail closed on the tested omissions, identity mismatch, reversed time, non-empty terminal state, and Boolean timestamp. It does not validate those assumptions against an X server. In particular, XSync completion is not proof of application consumption, keymap samples can miss transitions, and no task-useful effect or guard response was measured.

## Provenance limitation

The hypothesis, test, decision criterion, and deterministic fixture were described before the candidate. The source hashes were not frozen before execution; `SOURCE_HASHES.json` and this record bind the observed first outcome after the fact. Therefore this is **not** a prospectively source-frozen formal allocation. No rerun was made, and this outcome is not promoted beyond its exploratory construction scope.

## Environment / resource accounting

- Command: `python run_candidate.py`; then, in a separate process, `python audit.py`.
- Local Python: CPython 3.11.9.
- GPU: no model/CUDA work; RTX 3080 was observed at 0 MiB / 0% after this CPU-only test.
- Docker/WSL: no container or guest workload; Docker service-start attempts remained unsuccessful.
- Network, game, GUI, and input: none.
- Main identity recorded by both programs: `6cd70ad4bfad74e11658057bf024918bffb24add`.
