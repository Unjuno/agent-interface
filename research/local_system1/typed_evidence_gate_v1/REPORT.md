# Typed-evidence admission gate v1 — retained result

Task `LOCAL-SYSTEM1-TYPED-EVIDENCE-GATE-20260917-003`, Issue #912.

Decision: **PASS_TYPED_EVIDENCE_GATE_SCOPED**. Independent raw-array audit: **PASS**, errors 0. Formal case invocations 4/4, reruns 0; aggregate invocation 1.

## Frozen one-variable change

Relative to #906 DIRECT_TTC, confidence `>=0.90` remains necessary for early executable output. Candidate admission additionally requires current-stage class-prototype projection `>=3.5`, frozen before construction/formal as half the existing stress signal amplitude 7.0. Architecture, data generator, optimizer, epochs, widths/depths, distributions and retained gates remain fixed.

## First outcomes

| seed | stress premature DIRECT | stress premature gated | ordinary acc gated | stress acc gated | ordinary compute | stress compute | mean latency reduction vs FULL | p50 reduction | p95 regression |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 9101701 | 7 | 1 | 0.999756 | 0.989502 | 0.577454 | 0.734314 | 36.35% | 40.11% | -20.57% |
| 9101702 | 5 | 0 | 1.000000 | 0.988525 | 0.579590 | 0.730835 | 37.40% | 36.20% | -19.60% |
| 9101703 | 5 | 0 | 0.999756 | 0.987793 | 0.572021 | 0.721985 | 19.03% | 35.59% | 2.61% |
| 9101704 | 5 | 0 | 0.999756 | 0.985107 | 0.578918 | 0.721558 | 37.05% | 38.80% | -19.01% |

Aggregate: candidate stress premature is non-worse than matched DIRECT_TTC in all four seeds and strictly lower in all four here. Median mean latency reduction vs FULL is 36.70%; median p50 reduction is 37.50%; candidate mean is faster 4/4. Worst p95 regression is 2.61%, below the frozen +10% limit. No frozen violation remains.

## Scope

This is synthetic Python/PyTorch CPU evidence. The direct prototype projection is unusually available because the fixture generator explicitly defines the class signal. PASS supports the **architectural separation of learned prediction from deterministic typed admission evidence in this scoped mechanism**. It does not show transfer to an Astra-authored residual decision, real GUI control, token/economic gain, or external action authority. The next rung should test a real typed evidence field already available to the caller, rather than add another synthetic threshold.
