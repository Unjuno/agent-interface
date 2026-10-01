# Retained development failures / non-results

1. A first 300-repetition post-capture timing block exceeded the local execution envelope. It is not used for a performance claim.
2. An initial 60-repetition timing order showed a large `empty/full` anomaly inconsistent with the implementation delta; it was treated as cache/scheduling confounding and replaced by a paired randomized-order block. No robust empty/filled speed gain was retained.
3. The first digest-check assertion incorrectly required two distinct legal projections for the one-key `submitted` state. That assertion failed after computing the underlying rows. The corrected check limits the two-projection assertion to states with at least two required predicates. The primary 5/5 full-vs-scoped digest change is unaffected.
4. Two early admission-scope simulation revisions failed due fixture key mismatches before the final assertions. They are development harness failures, not scientific outcomes; the final v3 counterexample is represented by `admission_dependency_counterexample.py` in this branch.
5. Direct container download/clone of the frozen repository source failed DNS resolution. No substitute source was silently treated as the exact runtime. The block therefore uses retained repository evidence plus independent finite/replay checks and consumes no new live/formal allocation.
