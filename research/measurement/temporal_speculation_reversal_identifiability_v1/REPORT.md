# Result — #1194 pre-future reversal identifiability

Decision: **PASS_REVERSAL_NOT_IDENTIFIABLE_PRE_FUTURE_SCOPED**.

- retained source: merged #1134 raw SHA-256 `ee5d7f98...`
- deterministic invocation1; reruns/tuning0
- sequences64
- exact pre-future equivalence classes: **2** (L/R)
- each class: continue16 + reverse16
- Bayes-optimal exact-projection accuracy: **50%**
- ALWAYS_CONTINUE: continuation coverage32, reversal misses32
- ALWAYS_YIELD: continuation coverage0, reversal misses0
- maximum continuation coverage with zero reversal misses: **0**
- independent audit: PASS/errors[]
- future/mode leakage mutation: rejected

Method limitation is explicit: H/T/D/C/U were preregistered before a bounded schema sanity check, but the two balanced classes were observed before analysis-source freeze. The frozen result is therefore confirmatory/reproducibility evidence, not an unseen first peek.

Interpretation: for this deliberately aliased fixture, no decision rule restricted to current/history evidence can know whether a future reversal will occur. Adding a learned supervisor cannot recover absent information. Safe continuation requires either conservative YIELD or fresh post-current evidence. This does not claim real tasks are inherently unpredictable.
