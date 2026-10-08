# Issue #4844 preregistration — v1

## Status and lineage

- Successor to closed Issue #4155 (`FAIL_DIAGNOSIS_LAYER_UNNECESSARY`) and merged evidence PR #4169; the old source/result are immutable.
- Main intake: `cb717ebdcf14c2d0c87f5982395ac8ae70fdedbb` (2026-09-27).
- Issue: https://github.com/Unjuno/agent-interface/issues/4844
- Allocation: `typed-mode-generalization-4155-v1`; branch `research/typed-mode-generalization-4155-v1-20260927`.
- Intended additive path: `research/analysis/typed_mode_generalization_4155_v1/`.
- Formal allocation status: NOT RUN. Only construction and explicitly nonformal pilot seeds have been used.

## H — hypothesis

For partially observed, noisy binary cues and finite support, predicting a latent fault mode and aggregating its posterior through a fixed safe-disposition map can reduce wrong emitted recovery on each preregistered partial/compositional holdout by at least 25% relative to a direct disposition classifier, while losing no more than five percentage points of safe recovery coverage. The direction is not assumed: direct classification may benefit from pooled same-disposition modes.

## T — treatment and frozen data

- Pure deterministic model-free simulator; five modes, six binary cues, authored Bernoulli cue probabilities, no GUI/OS input, model/provider, network, user data, runtime authority, or GPU.
- Equal-information Bernoulli naive Bayes classifiers use identical support rows/features and Laplace alpha=1. `DIRECT_RECOVERY` predicts one of the mapped dispositions. `MODE_THEN_RECOVERY` predicts five modes, then sums the complete mode posterior by the frozen disposition map. Both emit YIELD unless top disposition posterior >=0.65 and margin >=0.15.
- Fixed map: FOCUS_LOST→REBIND; TARGET_STALE→YIELD; MODAL_BLOCKED and APP_BUSY→WAIT_OBSERVE; LAYOUT_CHANGED→REOBSERVE.
- Three disjoint support seeds `(415571,415572,415573)`, 96 rows/mode each. Three paired held-out seeds `(415581,415582,415583)`, 64 rows/mode/seed/block. Blocks: COMPLETE, SINGLE_MISSING, MULTI_MISSING, COMPOSITION_HOLDOUT, NUISANCE_SHIFT. Held-out total 4,800 rows. Training uses only COMPLETE support rows.
- Controls per held-out seed: five fixed complete-observation prototypes, all-missing unknown, and all-ones contradictory. Retain every latent label, feature mask/value, expected disposition, both predictions, posterior, confidence, and margin.
- Primary metric: wrong emitted recovery per row (wrong non-YIELD disposition; abstention is not counted as wrong recovery). Co-report wrong-disposition rate, safe recovery coverage, unnecessary yield, and full action confusion.
- Formal data are generated once into a fresh host output location, only after exact frozen package readback. Formal output is never deleted or overwritten.

## D — frozen decisions

- `PASS_TYPED_MODE_GENERALIZATION_SCOPED` only if all three blocks SINGLE_MISSING, MULTI_MISSING, and COMPOSITION_HOLDOUT individually show >=25% relative wrong-recovery reduction, <=0.05 absolute safe-coverage loss, and no increase in wrong recovery; COMPLETE prototypes match and unknown/contradictory controls yield in both arms; independent audit has zero errors.
- `FAIL_DIAGNOSIS_STILL_REDUNDANT` if valid integrity and no partial/compositional block passes the improvement gate.
- `FAIL_MODE_MISROUTES_RECOVERY` for any integrity-valid control misroute/prototype failure.
- `HOLD_COVERAGE_TRADEOFF` when a block improves wrong recovery but exceeds the coverage-loss bound.
- `HOLD_MIXED_PARTIAL_RESULT` for valid nonzero but insufficient/mixed improvements.
- `STOP_INFRASTRUCTURE_OR_PROVENANCE` for any pre-result source/image/invocation/audit provenance failure. No formal retry or post-hoc threshold/source change.

## C — construction, execution and audit

- Local Docker image `python:3.13.5-slim-bookworm`, image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, `linux/amd64`; already present locally.
- Use local CPU Docker only: `--pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges`; read-only source; separate fresh output mount. No workflows/Actions for research execution and no GPU.
- Separate auditor container, read-only source and raw input, fresh audit output; auditor independently regenerates data/model/predictions without importing `study.py`.
- Construction command used: `python -m unittest -v test_study.py` under the above container restrictions. Latest observed result: 6/6 PASS.

## U — interpretation limit

Only a synthetic authored Bernoulli fault family and this classifier factorization are tested. No conclusion about actual GUI diagnosis, cross-app transfer, learned model production utility, general architecture, safety/authority, latency/token benefit, human tempo, or runtime integration follows.
