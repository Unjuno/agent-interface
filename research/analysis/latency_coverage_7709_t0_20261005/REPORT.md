# Issue #7709 T0 — synthetic temporal-coverage method result

**Disposition: `PASS_METHOD_SCOPED`.** The independent raw-only audit exactly reconstructed 4,000 candidate replicate records across eight cells and all 1,152,000 paired windows. All 115,498 administratively censored windows were retained in the all-window denominator. Three frozen bad-result mutations were rejected.

**Scoped hypothesis result: `SUPPORTED_SCOPED`.** The attempt-i.i.d. nominal 95% t interval undercovered severely in this DGP (31.6–37.2% empirical coverage). The session-cluster interval covered the known all-window target in 92.8–96.4% of replicates in every cell. The six nonstationary cells improved coverage by 55.6–62.8 percentage points, exceeding the frozen 5-point threshold. In null cells, session-cluster false route promotion was 1.8–3.0%; the attempt-i.i.d. comparator falsely promoted the route in 31.2–34.8% of replicates.

| Synthetic case | Sessions | Pooled i.i.d. coverage | Session-cluster coverage | Gain | Pooled false promotion | Cluster false promotion | Mean detected boundaries |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stationary null | 8 | 31.6% | 96.4% | +64.8 pp | 32.6% | 1.8% | 2.370 |
| Stationary null | 16 | 36.8% | 94.2% | +57.4 pp | 33.0% | 2.4% | 1.324 |
| Abrupt-shift null | 8 | 32.6% | 95.0% | +62.4 pp | 34.8% | 3.0% | 2.596 |
| Abrupt-shift null | 16 | 33.0% | 95.2% | +62.2 pp | 31.2% | 2.6% | 2.132 |
| Warm-up null | 8 | 34.0% | 94.6% | +60.6 pp | 34.0% | 2.8% | 2.616 |
| Warm-up null | 16 | 33.4% | 94.8% | +61.4 pp | 34.8% | 3.0% | 1.984 |
| Gradual-drift benefit | 8 | 32.4% | 95.2% | +62.8 pp | n/a | n/a | 2.288 |
| Gradual-drift benefit | 16 | 37.2% | 92.8% | +55.6 pp | n/a | n/a | 1.694 |

## Interpretation and boundary

The coverage gain is attributable to using independent sessions as the inferential replication units, not to discovering segments: the segment-aware procedure reports within-run strata, weights them back to every original window, and then constructs the all-window interval from session-level integrated contrasts. Its all-window point estimate and interval changed by at most `4.27e-14 ms` under frozen no-boundary and extra-boundary partitions. This shows protection against arbitrary boundary choices when windows are retained; it does **not** validate the boundary detector.

The detector also proposed an average 1.324–2.370 boundaries in the stationary-null cells. That is a material over-segmentation warning: detected boundaries are descriptive and must not be treated as evidence of real performance regimes. This T0 does not assess detection sensitivity/specificity against causal regimes, does not tune the detector, and makes no general claim about real traces. The synthetic result is driven by intentional session-level route-slope variation and within-session autocorrelation, which make trial-level independence false by construction.

The all-window estimand is the paired `B−A` latency contrast with both arms assigned the declared 2500 ms cap on jointly censored windows. No timeout, warm-up, drift, shift, or other row was removed. The result does not invalidate historical route comparisons; each prior analysis needs its own design and trace audit. It does not establish any real route speedup, real temporal change, route correctness, safety, causal attribution, model/provider behavior, GUI/task effect, runtime change detector, or human tempo. T1 feasibility and T2 prospective validation remain open and require ordered traces, independent runs, and separate authorization.
