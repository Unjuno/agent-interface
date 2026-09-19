# Result — #1378 concurrent fast-decision T0 shadow

Decision: **PASS_T0_DETERMINISTIC_CONCURRENCY_SHADOW_SCOPED**.

- formal invocation1; reruns/replacements/tuning0
- fresh cases: **120,000**
- frontier schedule unchanged in all cases: request0 ms / return40 ms
- FRONTIER_BOUNDARY_ONLY deadline misses: **102,970 /120,000 = 85.808%**
- DETERMINISTIC_FAST_LANE deadline misses: **0 /120,000**
- deadline-miss improvement: **85.808 pp**
- deterministic disposition correctness: **100%**
- false ADVANCE on HARD_INVALIDATION: **0**
- output-envelope violations: **0**
- selector compute p50/p95/p99: **132 /169 /214 ns**
- whole local cycle p50/p95/p99: **2.500132 /2.500169 /2.500214 ms**
- correct local disposition frontier-open coverage: **88.883%**
- independent audit PASS/errors[]; corruption controls2/2
- raw RESULT SHA-256: `f0c203ce9651bfc1227462a4b5ecc69b8314d27379df63e41d4a9db6e03abdd9`

Interpretation: with frontier timing held fixed, this frozen typed-state fixture has a real reaction-deadline gap and a deterministic 5 ms local lane closes it without unsafe HARD continuation. There is no exposed classifier residual in T0, so the parent #1376 learned/Jev-like branch remains **HOLD_DETERMINISTIC_LANE_SUFFICIENT** rather than being promoted merely because a classifier is available.

Scope remains shadow-only: no actual Astra call, X11/task input, task-effect measurement, MAP01, or production timing claim.
