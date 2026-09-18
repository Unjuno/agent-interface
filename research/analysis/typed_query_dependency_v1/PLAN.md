# #1773 typed query dependency

## H
A complete path-specific query trace consists of the scope membership version plus value-version reads for every currently present member. Current-member reads alone miss phantoms; query version alone misses member-value mutation.

## T
Exhaustive standard-library formal over membership(A/B), value(A/B), unrelated u. Prepare once, then mutate membership A, membership B, value A, value B, or u. Compare DYNAMIC_QUERY, MEMBER_ONLY, QUERY_ONLY, STATIC_SCOPE, GLOBAL_EPOCH. One source-frozen formal invocation.

## D
PASS iff DYNAMIC_QUERY exactly matches ground truth for all 32 states with unsafe=0/false invalidation=0; MEMBER_ONLY and QUERY_ONLY unsafe>0; STATIC_SCOPE safe with false invalidations>0; GLOBAL_EPOCH more overinvalidating; empty/partial/full membership covered; audit/source integrity pass.

## C
Assumes one correct membership version. Writer-maintenance atomicity is not yet proved.

## U
Analytical query primitive only.
