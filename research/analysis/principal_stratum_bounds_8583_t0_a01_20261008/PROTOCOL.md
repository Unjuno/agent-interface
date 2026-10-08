# Frozen protocol — Issue #8583 T0 A01

The estimand is, separately within each policy, the mean binary recovery contrast `Y(A)-Y(B)` among finite-population units with demand under both policies. Demand and outcomes are potential values under each policy; outcome entries are undefined when that policy has no demand. Available observations are only aggregate demand counts and recovery successes under each policy/option.

The candidate enumerates multisets of all legal unit types and retains those exactly matching every margin. For each policy, it computes the minimum and maximum exact-rational always-demand contrast over compatible tables with a nonempty always-demand stratum. It also records whether a compatible table has an empty always-demand stratum; in that case identification is explicitly `UNIDENTIFIED_EMPTY_STRATUM`, even when the nonempty-table bounds collapse to a point. A zero policy demand makes that policy's observed contrast null, never zero.

The auditor independently enumerates ordered assignments, checks legality/margins, canonicalizes to unlabeled tables, rebuilds all results, and compares them with the sealed hand-derived truth. Mutation controls alter a bound, assert demand monotonicity, fill an undefined outcome, omit a completion, or falsely claim point identification. Each must be rejected.

All inputs are authored toy data (population sizes 2–3), not sampled observations. No uncertainty interval, general identification theorem, or empirical causal effect is estimated. No assumption beyond the listed margins and binary-variable support is introduced. The experiment cannot establish anything about real policies, people, software behavior, or product value.

One-shot order: frozen source/data/tests/docs → manifest/hash check → committed freeze → candidate once → auditor once conditional on candidate exit 0 → hash raw evidence → report. Any failure is terminal and retained; no reruns, repairs, or replacement outcomes within A01.
