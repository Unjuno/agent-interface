# Issue #7709 T0 — finite coverage experiment

## Disposition

The frozen synthetic gate returned `METHOD_PASS_SCOPED`. In 240 null-effect datasets per workload, conventional row-independent intervals covered the true zero contrast in only 29.6% (stationary), 31.7% (abrupt shift), and 32.5% (gradual drift). The frozen session-cluster t intervals covered it in 93.3%, 94.2%, and 93.3%, respectively; cluster false-promotion rates were 6.7%, 5.8%, and 6.7%. The independent auditor v2 passed 8/8 checks, including complete denominator/pairing reconstruction, all four row/boundary mutations, and independent recomputation from the 230,400-row raw ledger.

| Workload | Pooled row coverage | Session-cluster coverage | Gain | Cluster false promotion |
|---|---:|---:|---:|---:|
| Stationary | 29.6% | 93.3% | 63.8 pp | 6.7% |
| Abrupt shift | 31.7% | 94.2% | 62.5 pp | 5.8% |
| Gradual drift | 32.5% | 93.3% | 60.8 pp | 6.7% |

## What this does and does not establish

This finite result shows that, under the frozen design's strong within-session autocorrelation and session-specific treatment heterogeneity, treating 40 attempts as independent can severely understate uncertainty. The session-cluster interval retains the all-window route contrast and its independently initialized session as the inferential unit. The common workload path includes a stationary control, an abrupt change, and gradual drift; 5% censored attempts are retained at the declared 120 ns deadline penalty rather than dropped.

The experiment does **not** establish that real Agent Interface trials have these regimes, that session clustering is the right unit for any specific route study, or that any route is faster. It uses a frozen four-block time grid and checks block labels, but does not validate a data-driven change-point selector or establish regime-specific causal effects. Therefore `METHOD_PASS_SCOPED` applies to this synthetic all-window coverage method only; the broader segment-selection and real-trace feasibility questions in #7709 remain open.

No prior route result was regraded. No model, GUI, application, input, GPU, WSLc, or Docker was used. Issue #7709's T0 explicitly permits CPU-only simulation; the separate OrbStack inventory query failed before any container launch.

## First audit failure retained

The candidate ran once and produced `METHOD_PASS_SCOPED`. Independent audit v1 returned `AUDIT_FAILED` 4/5 because it computed false-promotion rate as `1 - rounded_coverage`; that floating-point path differed in the last bit from the candidate's direct Boolean count. The candidate and raw ledger were not rerun or changed. A separately frozen raw-only audit v2 counted false promotions directly and passed 8/8. Both audit records and their source digests are retained; v1 was not overwritten.

## Reproduction

From the repository root, the candidate is intentionally write-once and the 45 MB JSONL ledger is hash-bound in `RESULT.json`:

```sh
python3 -B research/analysis/latency_regime_coverage_7709_t0_20261005/candidate.py
python3 -B research/analysis/latency_regime_coverage_7709_t0_20261005/audit.py
python3 -B research/analysis/latency_regime_coverage_7709_t0_20261005/audit_v2.py
```

The first audit's expected failure is part of the history; the candidate must not be invoked again when its output exists. Exact digests are in `SHA256SUMS`.
