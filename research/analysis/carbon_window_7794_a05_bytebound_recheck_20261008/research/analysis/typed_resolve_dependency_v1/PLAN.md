# #1767 typed resolve dependency

## H
For alias preparation, the minimal complete dynamic dependency trace is the alias mapping identity/version plus the selected concrete object identity/version. Tracking only either component is unsafe.

## T
Exhaustive standard-library formal over alias target A/B and binary A/B/u values. Prepare once, then mutate one of mapping/A/B/u. Compare DYNAMIC_RESOLVE, CONCRETE_ONLY, ALIAS_ONLY, STATIC_BOTH, GLOBAL_EPOCH. Ground truth is typed dependency identity. One source-frozen formal invocation.

## D
PASS iff DYNAMIC_RESOLVE exactly matches ground truth in all 16 states with unsafe=0/false invalidation=0; CONCRETE_ONLY and ALIAS_ONLY each unsafe>0; STATIC_BOTH safe with false invalidations>0; GLOBAL_EPOCH more overinvalidating; both targets covered; audit/source integrity pass.

## C
No query/phantom, multi-hop alias, cycle, or writer-maintenance atomicity.

## U
Analytical primitive only.
