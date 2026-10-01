# #1675 Exact dependency-version criterion for safe compute reuse

TASK: `EVIDENCE-DEPENDENT-COMPUTE-REUSE-ANALYTIC-R0-20260918-001`

Parent #1663. One semantic question only: when may a generic scheduler reuse a cached deterministic pure computation from evidence-version metadata alone?

## H
If the job is a deterministic pure function of a complete declared dependency set and each dependency has a non-reused semantic version identity, exact dependency-version-vector equality is sufficient for reuse. For universal safety over arbitrary deterministic jobs it is also necessary: any changed declared dependency admits a valid discriminator function. If a true dependency is omitted, declared-vector equality is insufficient.

## T
Exact proof plus exhaustive finite confirmation over four Boolean evidence items, all 16 declared subsets, and all 256 source/current state pairs per subset. Construct one discriminator witness for every declared mismatch and one hidden-dependency counterexample for every `(declared subset, omitted bit)` pair. Independent audit recomputes counts and witnesses from constants.

## D
PASS iff all exact matches are safe under assumptions, all declared mismatches have a discriminator, all hidden-dependency controls falsify incomplete declarations, empty dependency is safe only as a constant/pure job, corruption controls reject, and formal1/reruns0/replacements0/tuning0.

## C
Token reuse/ABA, hash collision, incomplete dependency declarations, nondeterminism, time/external state, or side effects violate assumptions and can make version equality unsound.

## U / stop
Semantic theorem only; no scheduling, latency, CPU saving, model quality, runtime ABI or product claim.
