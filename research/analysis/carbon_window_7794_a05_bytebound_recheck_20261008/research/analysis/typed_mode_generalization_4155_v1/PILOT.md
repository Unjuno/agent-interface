# Nonformal construction pilot — Issue #4844 v1

Status: preformal diagnostic only; not an estimate and not part of the formal allocation. It used construction-only seeds support `(415001,415002,415003)` and held-out `(415011,415012,415013)`. These seeds are disjoint from and do not replace the frozen formal schedule. No source/gate was tuned from formal observations because formal observations do not exist.

Independent audit result: `HOLD_MIXED_PARTIAL_RESULT`, `errors=[]`. Unknown and contradictory controls yielded in both arms for all 3/3 held-out seeds; complete prototype mismatches were 0.

Pooled descriptive metrics across these diagnostic seeds:

| Block | Direct wrong recovery | Mode wrong recovery | Direct safe coverage | Mode safe coverage |
|---|---:|---:|---:|---:|
| SINGLE_MISSING | 150/960 (15.625%) | 168/960 (17.500%) | 0.128125 | 0.193750 |
| MULTI_MISSING | 77/960 (8.021%) | 74/960 (7.708%) | 0.247917 | 0.263542 |
| COMPOSITION_HOLDOUT | 211/960 (21.979%) | 219/960 (22.813%) | 0.132292 | 0.202083 |

The mode arm is worse on single-missing and compositional holdout, and only marginally better on multi-missing. Therefore the direction is plausibly negative; the frozen formal study remains discriminatory because it can confirm scoped redundancy or isolate a block-specific effect, but may return an expected FAIL/HOLD. No threshold changes, sample-size inflation, retries, or claims are justified by this pilot. Full/nonformal raw pilot output was not generated into the formal artifact location.
