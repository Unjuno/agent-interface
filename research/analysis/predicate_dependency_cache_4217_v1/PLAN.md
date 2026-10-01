# Predicate dependency cache v1 — Issue #4217

Allocation: `predicate-cache-4217-20260923-01`

## H
Dependency-scoped predicate caching can reduce semantic evaluator calls on a fixed repeated-observation trace while exactly preserving predicate and graph outcomes, if every cache entry binds the predicate's declared dependency generations plus intent version, producer version, and source generation/currentness.

## T
Authority-neutral deterministic replay in the provided Linux container, CPython standard library only. Four predicates over one frozen 13-state trace. Compare RECOMPUTE_ALL versus PREDICATE_CACHE. The trace includes unrelated mutation, relevant mutation, semantic ABA restoration with a new generation, intent-version change, producer-version change, dependency UNKNOWN, stale source, fresh source generation replacement, last-effect change, target change and restoration, and another unrelated mutation. One formal invocation; no rerun/replacement/tuning.

## D
PASS_DEPENDENCY_SCOPED_PREDICATE_CACHE_SCOPED only if: all 13 states/52 predicate observations reconcile; cached predicate values equal full recomputation everywhere; graph dispositions match everywhere; no authority is granted; cache has at least 8 hits and at least one hit on an unrelated-only change; every relevant dependency/intent/producer/source/UNKNOWN/ABA control causes the required miss/invalidation; evaluator calls are strictly fewer than 52; raw-only audit errors=[]; >=10 copied-evidence mutations reject. Complete semantic mismatch is FAIL_FALSE_PREDICATE_REUSE; no useful hits is FAIL_INVALIDATION_TOO_BROAD; missing provenance/process/raw/audit is STOP/HOLD.

## C
The evaluator is deterministic and authored; this tests applicability semantics, not model nondeterminism or natural GUI change distributions. A whole-policy cache may be simpler in other tasks.

## U
No live authority, cross-session persistence, model/provider, GUI/input, task benefit, token saving, production latency, or generalization claim. Lookup timing is descriptive only and not a promotion gate.
