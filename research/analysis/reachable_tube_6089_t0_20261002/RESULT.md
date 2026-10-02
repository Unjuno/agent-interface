# Result — Issue #6089 T0 reachable-tube method fixture

**Disposition: `PASS_METHOD_SCOPED`**, bound strictly to the eight frozen integer fixtures and the declared disturbance alphabets in `cases.json`. This is a finite method-consistency result, not an empirical controller-benefit result and not evidence that any real system's disturbances are bounded.

| Fixture | Robust selected horizon | Nominal-point horizon | Result note |
|---|---:|---:|---|
| narrow corridor | 4 | 5 | uncertainty plus release lag shortens the nominal choice |
| wide initial uncertainty | 2 | 5 | wider starting set shortens the robust choice |
| safe long corridor | 5 | 5 | reaches frozen horizon cap |
| near boundary | 0 | 1 | robust policy yields where nominal would hold |
| moving forbidden boundary | 2 | 5 | all-prefix check catches the tightening boundary |
| invalidated target | 0 | 0 | fail-closed `YIELD_INVALIDATED_SOURCE` |
| zero-slack release | 0 | 0 | release-lag prefix leaves no positive certified hold |
| disturbance-bound violation stress | 2 | 5 | stress trajectory crosses the boundary and is explicitly `OUT_OF_ENVELOPE_NOT_CERTIFIED` |

The independent recursive path enumerator returned `PASS_METHOD_SCOPED`, errors `[]`, and exact row-by-row agreement with the set-propagation candidate. Construction tests passed 3/3, including all five preregistered raw-record corruptions rejected. Formal candidate and separate auditor each ran once; retries 0.

## Interpretation

The fixtures show the intended method discriminator: nominal-point horizon selection can overestimate the robust choice, while a safe corridor preserves a longer horizon. The method also refuses on invalidation and zero slack. The out-of-envelope stress is intentionally not covered by the certificate; no safety claim is made for it. A simple fixed short hold may still be preferable in real systems, and the result says nothing about whether this selector improves task outcomes or observation cost in GUI/DOOM.

No model, training, adapter update, GPU/CUDA, Docker/WSLc container, network access during candidate/audit, GUI, game, or user-input effect occurred. The experiment used local Windows host CPU only. It does not close #59's live threat-control or MAP01 requirement.

Raw files: `candidate_raw.json` (SHA-256 `9c7763a896e6e92bb776eabd0d3cc67e1620fb0572db10b19312bf69648833ff`) and `audit.json` (SHA-256 `5dc0bdd0180b721caf9d3cbbea8254fef6ac3d0c361d1178dc2e2bfa227fbf96`). Complete checksums are in `SHA256SUMS`.
