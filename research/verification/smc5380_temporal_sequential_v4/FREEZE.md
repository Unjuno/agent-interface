# Issue #5380 T0-v4: temporal trace / SPRT method calibration

Allocation: `smc5380-temporal-sequential-v4-20260930-01`
Branch: `research/smc5380-temporal-sequential-v4-20260930-01`
Path: `research/verification/smc5380_temporal_sequential_v4/`
Frozen main: `0154e7533fb76a67578e0b2789aa42c32a511369`

## H / T / D / C / U

**H.** A fault-stratified Wald sequential test, paired with an explicit time-bounded trace property, can distinguish a 1% null violation rate from an injected 8% rate under the stated IID generator; repeated calibration replications should bound the false-fail rate and detect injected risk at the predeclared thresholds, while preserving every counterexample seed.

**T.** The temporal property is: before tick 2, no unverified action is admitted and a safe trace must reach typed UNKNOWN or CONTAINMENT. Five strata: timeout, stale receipt, duplicate result, correlated verifier, dropped ACK. Injected violation rates are 1% in four strata and 8% in correlated-verifier. Compare a fixed 20/stratum replay, a 1,000-trace weighted-uniform sample, and separate per-stratum Wald SPRTs. SPRT parameters: H0 p0=.01, H1 p1=.08, alpha=.05, beta=.10, max 500 samples/stratum. Calibrate with 2,000 independent SPRTs at p0 and 2,000 at p1. No adaptation or rerun.

**D.** Method calibration PASS only if: 95% Wilson upper bound for false FAIL at p0 <=.08; 95% Wilson lower bound for FAIL detection at p1 >=.85; inconclusive rate <=.02 under p0 and <=.15 under p1; correlated-verifier stratum reaches FAIL; all observed temporal violations retain their seed; and the pre-frozen independent audit reports no errors. Otherwise retain the exact FAIL/UNCERTAIN. This does not estimate any deployed-system rate.

**C.** IID Bernoulli draws within each declared stratum, independent replication seeds, frozen weights for the uniform comparator, and a generated safe fallback. The fixed replay and pooled uniform rate are descriptive comparators, not valid claims about an unspecified deployment distribution. The per-stratum test avoids using their pooled mean to hide the injected high-risk class.

**U.** Synthetic generator and known injected rates only; no real system, model, authority runtime, task, GUI, rare-event guarantee, non-IID validity, calibration outside p0/p1, multiplicity correction for five simultaneous strata, or universal safety claim. The injected action is a simulated event only, never an OS/UI action.

## Exact pre-run source identities (Git blob SHA-1)

- Core: `f0d07ea839bc4e8b80bb9d10b9640e6c03e4aa55`
- Runner: `8276bd4fb280b370956db20e6e6268fb04eb78d8`
- Tests: `cb20c71a41e587f8fa3649e06e32663d1fae3e64`
- Independent auditor (frozen before formal invocation): `9f64916fe96de99715d6c7021a9d2d9c3171e452`
- Retained construction-01 failure: `318998471bfdcc44766e14fc5ecf6ceb48c992a2`

Construction-01's floating-point assertion failure is preserved as-is. Construction-02 ran the corrected 9-test suite with 9/9 passing before this freeze. Formal T0 is one runner invocation and one auditor invocation only.

Execution is host CPython 3.11.9, memory-streamed from GitHub readback with `python -B`; no local output file. C: had 0 bytes free. Current #5085 policy prohibits Docker CLI pending exact owner release and queue allocation; no container/GPU/model/network/GUI/input or real action will be used. The raw must say `container:false`.
