# #1782 query-version writer atomicity

## H
A query-version validator is safe and non-overinvalidating only when membership mutation and query-version increment are published atomically. Membership-first exposes an unsafe stale-query window; version-first is safe but exposes a false-invalidation window; no-version is persistently unsafe.

## T
Exhaustive standard-library state-transition formal over initial membership m in {0,1}. Reader is prepared at (m,q0) and validates by q equality. Enumerate every externally visible stage of ATOMIC, MEMBERSHIP_FIRST, VERSION_FIRST, NO_VERSION. Reader validate+commit is one linearized boundary. One source-frozen formal invocation.

## D
PASS iff ATOMIC unsafe=0 false=0; MEMBERSHIP_FIRST unsafe>0; NO_VERSION unsafe>0; VERSION_FIRST unsafe=0 false>0; insertion and removal both covered; audit/source integrity pass.

## C
Version-first is safety-preserving but loses precision/liveness. Multi-writer transactions, durability and crash recovery are outside scope.

## U
Finite publication-order primitive only.
