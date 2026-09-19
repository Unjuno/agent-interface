# #1756 typed dynamic branch read-set

## H
For one deterministic branch, tracing the control read plus only the executed data read reconstructs the minimal path-specific read set. Omitting the control read is unsafe; tracing the unexecuted branch or unrelated resources is safe but over-invalidating.

## T
Exhaustive standard-library formal over binary g/a/b/u. Prepare once, then apply one versioned mutation to each resource. Compare DYNAMIC_TYPED, DATA_ONLY, FULL_STATIC, GLOBAL_EPOCH. Ground truth is path-specific dependency identity. One source-frozen formal invocation.

## D
PASS iff DYNAMIC_TYPED exactly equals ground truth for all 16 prepared states, has unsafe=0 and false invalidation=0; DATA_ONLY unsafe>0; FULL_STATIC safe with false invalidations>0; GLOBAL_EPOCH false invalidations exceed FULL_STATIC; both branches covered; audit/source integrity pass.

## C
Only executed simple branches are covered. Alias resolution, queries/phantoms, and writer-maintenance atomicity remain separate rungs.

## U
Analytical primitive only; no shared runtime/API promotion.
