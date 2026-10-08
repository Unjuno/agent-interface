# Issue #8582 T0 A01 — result

## Disposition

`PASS_METHOD_SCOPED`. The frozen candidate and independent auditor each ran once; no retries. The auditor reconstructed 18,000 assigned item responses across eight scenarios, passed 18,064 checks, and rejected all 7 mutation controls. Candidate raw SHA-256: `1922744ee6ad38b7ca9b046683fe1792b5a6c0d68d0f07c4d2bee608cfd268f1`.

## Results

- Uniform DIF: the planted `target_uniform` item was flagged with a +0.30 agent-minus-human response difference in both capability strata.
- Nonuniform DIF: the planted `target_nonuniform` item was flagged with +0.30 in the low stratum and -0.30 in the high stratum.
- Invariant and placebo-label cases left null and target items unflagged. The zero-discrimination item returned `LOW_INFORMATION`.
- The composition-invariant fixture remained equal-mix across groups; it does not test marginal composition confounding.
- No common support returned `HOLD_COMMON_SUPPORT`; shifted anchors returned `HOLD_ANCHOR_INVALID`.
- In the missingness case, all 2,400 assigned rows remain counted; 50 outcomes are UNKNOWN, and the target item returns `UNKNOWN_LOW_SUPPORT` rather than being imputed or certified.

## Scope and limitation

This validates a deterministic conditional-contrast scorer on strong authored binary effects. It does not fit an ordinal/logistic DIF model, estimate uncertainty or multiplicity-adjusted population effects, or establish a real human–agent measurement difference. It does not support fairness, latent-mean comparability, accessibility, superiority, or participant-study claims. No participants, model, GUI, or external service were used; authority is `NONE`.

## Custody correction

After the formal run, a composition-only scenario was explored in construction code. Those edits were accidentally included in an intermediate branch commit together with the already completed result files. No candidate or auditor was run against the edited code. Before packaging the result, every frozen source file was restored byte-for-byte from the preregistered commit `05f180a5dcfcde4f27fa121ae7e63de42d15e33d`; all source hashes in `FREEZE.json` now match. The later composition-only edits are excluded from this result and are not scientific evidence. The formal raw/audit pair remains tied to the original eight-scenario freeze; the allocation was not rerun.

## Provenance

Preregistration: [Issue #8582 comment](https://github.com/Unjuno/agent-interface/issues/8582). Frozen inputs: commit `05f180a5dcfcde4f27fa121ae7e63de42d15e33d`, base main `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`. Candidate and audit logs, exits, timestamps, raw outputs and hash manifest are retained under `results/`. See [FREEZE.json](FREEZE.json), [PLAN.md](PLAN.md), [spec.json](spec.json), and [SHA256SUMS.json](SHA256SUMS.json).
