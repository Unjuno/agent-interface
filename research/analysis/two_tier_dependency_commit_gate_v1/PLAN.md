# #1835 two-tier dependency + commit gate

## H
Prepared reusable dependencies and fresh commit-time gates are distinct temporal roles. Safe admission requires both:
- every prepared dependency remains current; and
- a fresh lineage-bound gate is current and TRUE/LIVE.

Using only either layer, or caching a prepare-time TRUE gate for commit, is unsafe. Treating all evidence as one undifferentiated scalar-current condition can be safe but over-conservative.

## T
Exhaustive standard-library formal over 24 states:
- dependency currentness: current/stale;
- fresh gate truth: TRUE/FALSE/UNKNOWN;
- fresh gate lineage/currentness: current/stale;
- prepare-time cached gate: TRUE/FALSE.

Compare TWO_TIER, DEP_ONLY, GATE_ONLY, CACHED_GATE, SCALAR_ALL_CURRENT. Oracle equals exact two-tier semantics. Retain explicit unsafe witnesses. One source-frozen formal invocation.

## D
PASS iff TWO_TIER mismatch0/unsafe0; DEP_ONLY/GATE_ONLY/CACHED_GATE each unsafe>0; at least one valid row admits; stale-lineage/FALSE/UNKNOWN fresh gates admit0 under TWO_TIER; SCALAR_ALL_CURRENT has unsafe0 but false rejection>0; role/lifetime labels are retained; audit/source/invocation integrity pass.

## C
An implementation may fuse layers into one opaque token only if it preserves both prepared dependency provenance and a fresh commit-bound gate.

## U
Finite admission semantics only; no GUI/model/input/latency claim.
