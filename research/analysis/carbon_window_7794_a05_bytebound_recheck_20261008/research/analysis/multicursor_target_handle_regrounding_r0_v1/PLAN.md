# #1682 Plan — fresh multi-target handles versus semantic re-grounding

TASK: `MULTICURSOR-TARGET-HANDLE-REGROUNDING-R0-20260918-001`  
BASE: `33d09739589f80c5e4bfda22bdfcff39377b81fe`  
Parents: #1643 / PR #1649, #1654

## H
Partition accesses into explicit freshness epochs. Epoch changes invalidate every cached handle. Within one epoch, a one-handle cache misses on the first access and each target switch, while an unbounded associative fresh-handle cache misses once per distinct target. Hence maximum retention saving is the one-handle miss count minus per-epoch distinct-target count. Strict saving exists iff a target is revisited non-consecutively within the same epoch.

## T
Deterministic standard-library enumeration over every target sequence of lengths 1..7 on {A,B,C} and every binary epoch-boundary schedule. Compare operational LRU k=1,2,3 and unbounded caches, all cleared on each epoch boundary, against independently expressed closed forms for k=1 and unbounded. Check stale cross-epoch hits, strict-saving equivalence, LRU stack monotonicity, and canonical controls. Independent audit re-enumerates without importing the candidate.

## D
PASS scoped iff formula mismatches=0, strict-equivalence mismatches=0, stale cross-epoch hits=0, unbounded>worse-than-one violations=0, LRU monotonicity violations=0, positive k=2 gain is non-vacuous, an epoch-reset no-gain control is retained, and independent audit/corruption controls pass.

## C
Target identity resolution may itself require a model; geometry may drift inside an under-specified epoch; validation overhead can dominate saved grounding; finite-cache policy matters; stable application IDs/APIs may subsume visible multi-cursors; physical-device concurrency remains #1643.

## U
Discrete cache/currentness semantics only. No measured model tokens, wall-clock latency, GUI correctness, human tempo, or runtime recommendation.

## Stop
One source-first frozen bounded result and independent audit. No model/GUI/runtime allocation.
