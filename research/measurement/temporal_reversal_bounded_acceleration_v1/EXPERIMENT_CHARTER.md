# TEMPORAL-REVERSAL-BOUNDED-ACCELERATION-R1-20260918-008

## H
With the exact #1311 bounded-interval estimator and the calibrated nominal per-sample error bound B1000 fixed, modest bounded post-reversal acceleration should remain fail-closed: it may increase UNKNOWN, but must not fabricate the wrong current direction. The zero-acceleration arm must reproduce #1319 B1000 exactly.

## T
Hold cadence=10 Hz, history=500 ms, one reversal, deterministic ±1000 micro-unit per-sample jitter, sample schedule, estimator, B1000 tolerance and formal ages {25,50,75,100,150,200} fixed. Change only post-reversal acceleration expressed as fractional velocity change per 100 ms: {-0.02,-0.01,0,+0.01,+0.02}. Pre-reversal motion remains unit speed. Post-reversal speed remains positive throughout the frozen horizon.

Formal: 6 ages × 2 post directions × 100 phases × 5 acceleration arms = 6000 rows, one invocation, reruns/replacements/tuning0. Construction uses disjoint ages/phases only.

## D
PASS_BOUNDED_ACCELERATION_REVERSAL_SAFETY_SCOPED iff:
1. A0 reproduces exact #1319 B1000 accuracy {25:.240,50:.495,75:.740,100:.995,150:1.000,200:.985} and wrong-direction0;
2. every acceleration arm has wrong-direction rate0 at every age;
3. at ages {50,75,100,150,200}, each nonzero-acceleration arm accuracy is >= 90% of A0 at the same age;
4. no output grants authority/task input; source/audit/corruption integrity passes; invocation1/reruns0.

Any wrong direction under a nonzero acceleration arm is FAIL_BOUNDED_ACCELERATION_SAFETY. If wrong-direction remains0 but the 90%-of-A0 coverage gate fails, HOLD_ACCELERATION_INCREASES_ABSTENTION. A0 reproduction/source mismatch is FAIL_INTEGRITY.

## C
This is authored constant acceleration only after reversal. Acceleration magnitude is small and known only to the generator, not the estimator. Correlated bias, multiple reversals, dropped samples, real pixel localization and unknown error envelopes remain excluded.

## U / stop
Synthetic observation contract only. No GUI/model/task-control/runtime claim. Stop after one source-first 6000-row block plus independent audit. If PASS, the next realism factor is real-pixel localization error/cadence with estimator and nominal bound fixed; do not change localization and estimator simultaneously.
