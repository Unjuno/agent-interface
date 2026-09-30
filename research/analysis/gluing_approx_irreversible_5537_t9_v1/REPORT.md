# Issue #5537 T9 — audit pass, policy-coverage HOLD

**Disposition: `HOLD_SCOPE_GAP`; do not promote the audit's mechanical PASS to a scientific PASS.** The candidate emitted a fully auditable 135-row matrix and the independent oracle found zero baseline discrepancies; all six non-identity mutations were rejected. A post-run semantic coverage review found that the preregistered matrix did not actually exercise its declared `beyond_tolerance` condition and that the `exact_only` contract admitted approximate reversible/compensable actions. Preserve the raw and audit exactly as run.

## H / T / D / C / U

- **H:** A typed gluing status and explicit action contract can keep approximate evidence useful for reversible/compensable actions while refusing irreversible admission by default; an opt-in contract is distinct.
- **T:** One current-main host-local matrix over five named cases, three tolerance values, three contract labels and three action classes. Candidate enumerated eight binary assignments per row; independent bitmask auditor replayed 135/135 rows and six preconditioned corruption controls. The intended wider T matrix is not fully covered: tolerance values were `{0, 0.5, 1}` against spread `0.5`, so no case had `spread > tolerance`. Also, `exact_only` rows admitted approximate reversible and compensable actions.
- **D:** Mechanical gate passed: runner exit 0; audit exit 0; 135 rows; base errors `[]`; six of six non-identity controls rejected. **Scientific promotion gate is HOLD** because the true beyond-tolerance arm was absent and contract semantics were not separated as named. Do not infer behavior for that missing region.
- **C:** CPython 3.14.5/macOS arm64 host-only; finite binary relations and hand-authored scalar spread/tolerance. No Docker lease, GUI, model, network, or external effect.
- **U:** No empirical tolerance calibration, authenticated action contract, general sheaf solver, live evidence, real irreversible action, safety or production claim. T5–T8 records are unchanged.

## Reproduction and hashes

- Base main: `94dbdc8a04a78eb5dc6089058e74b7cec31bbdc4`.
- Candidate: `python3 -B run_experiment.py`, one invocation, exit 0, 135 rows.
- Raw SHA-256: `461846364c00494ea429f03ed6fd11b46121b7f7be8053f4c1258faa050a19e1`.
- Independent audit: `python3 -B audit_raw.py`, one invocation, exit 0, `PASS_APPROXIMATE_IRREVERSIBLE_GATE_SCOPED`, base errors `[]`, 6/6 non-identity mutations rejected.
- Audit JSON SHA-256: `63775ac0878278b0dcb4176b80f8e3e62dfb02313e6c84e000a5477b0f8ee9de`.
- Candidate SHA-256: `98a8748c8121e0f2feeb305842a542a6072ea2997abce39589de51c9915ae8b7`.
- Runner SHA-256: `33705b75fff66cd14f15f701573a28435ad8ff6bbd202523b0641fc459b343e7`.
- Auditor SHA-256: `1abcf8adb15fc3e638fd43618655cfa9ae155c558ab5ed5697081610fd46b7de`.
- Construction tests: 3/3; `py_compile` passed. The first test attempt from repository-root cwd failed import resolution; rerunning from the frozen allocation cwd passed without code change.

Any complete policy comparison needs a fresh allocation with explicit distinct contract semantics and at least one tolerance strictly below the fixed positive spread. T9 raw/audit must not be rewritten or rerun.
