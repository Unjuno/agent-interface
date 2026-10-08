# #1895 Right-censored dwell-time identifiability result

Decision: **PASS_PROBABILISTIC_AUTOMATON_DWELL_CENSOR_SCOPED**

For integer dwell duration observed only when D<=T, completion-only durations do not identify the full dwell distribution or mean once positive right-censor mass exists.

Formal known-support case: T=4, trusted maximum M=8, exact mass denominator N=8. All C(15,7)=6,435 duration distributions over1..8 were enumerated and grouped by completed masses at1..4 plus total censor mass.

- distributions: 6,435
- observable groups: 495
- group mean-range mismatch versus analytic bound: 0
- endpoint sharpness failures: 0
- ambiguous observable groups with >1 full mean: 330
- completion-only mean defined with positive censor mass: 6,105
- completion-only mean different from full mean: 6,105/6,105
- completion-only underestimation sign mismatch: 0
- censor-at-horizon imputation underestimation rows: 6,270
- censor-at-horizon sign mismatch: 0

With known M the sharp mean interval is completed-mass moment plus censor_mass times [T+1,M]. Both endpoints are attainable by concentrating censored mass at the minimum or maximum allowed tail duration.

Without a trusted finite maximum, the same retained evidence has no finite upper mean bound. A fixed observation with half the mass completed at duration2 and half censored has means5,9,17,33 when the censored mass is placed at durations8,16,32,64 respectively, while its observable completed/censored evidence is unchanged.

Implication for #1658: dwell-time statistics must retain right-censor information. Averaging completed transitions or imputing the timeout itself as the dwell duration systematically understates the dwell mean in this scoped model.

Source-first canonical readback matched3/3 before formal. Independent audit reproduced all counters. Formal invocation1; reruns/replacements/tuning0.

Scope: discrete population-level identifiability only. No sampling uncertainty, continuous-time survival model, real GUI dwell estimate, prediction quality, latency or product claim.
