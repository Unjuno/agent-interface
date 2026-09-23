# #1682 Fresh multi-target handles vs semantic re-grounding

Decision: **PASS_MULTITARGET_HANDLE_REGROUNDING_SCOPED**.

## Result

A complete bounded enumeration covered **167,961 traces** and **1,142,139 target accesses**: every target sequence of lengths 1..7 over `{A,B,C}` crossed with every binary freshness-epoch boundary schedule.

- closed-form vs operational cache mismatches: **0**;
- strict-saving equivalence mismatches: **0**;
- stale cross-epoch hits: **0**;
- unbounded-cache-worse-than-one-handle violations: **0**;
- LRU stack monotonicity violations (`M3 <= M2 <= M1`): **0**;
- traces with strict `k=2` gain vs one handle: **41,994**;
- traces with strict `k=3`/unbounded gain: **46,662**;
- independent full re-enumeration: **PASS**;
- fixed corruption controls rejected: **4 / 4**.

Across the bounded corpus, total misses were `979,776` for one handle, `928,266` for LRU-2, and `919,542` for LRU-3/unbounded. These totals are corpus diagnostics, not workload-weighted product forecasts.

The maximum bounded per-trace saving was **5 re-groundings** on `A,B,A,B,A,B,A` in one epoch: one handle misses 7 times; an associative cache holding both targets misses 2 times.

## Analytical proof

### Variable table

| Symbol | Meaning | SI unit | Definition | Domain / assumptions | Type |
|---|---|---:|---|---|---|
| `i` | access index | 1 | position in the target-access trace | integer `1..n` | scalar integer |
| `a_i` | requested semantic target identity | none | target requested at access `i` | categorical; identity is already resolved | categorical scalar |
| `e_i` | freshness epoch / binding generation | none | currentness generation attached to access `i` | categorical/integer; a change invalidates all older handles | categorical/integer scalar |
| `M_1` | one-handle re-grounding misses | 1 | misses of an LRU cache of capacity 1, cleared on epoch change | nonnegative integer | scalar integer |
| `M_k` | `k`-handle LRU misses | 1 | misses with capacity `k`, cleared on epoch change | `k >= 1` | scalar integer |
| `M_inf` | unbounded fresh-handle misses | 1 | one miss for each distinct target within each epoch | nonnegative integer | scalar integer |
| `S` | maximum retained-handle saving | 1 | `M_1 - M_inf` | nonnegative integer under this model | scalar integer |
| `c_g` | cost of one real semantic re-grounding, if later measured | s, tokens, or another declared cost unit | external per-miss cost, not measured here | must use one homogeneous unit per analysis | scalar real |

Consider one freshness epoch with target sequence `a_1,...,a_m`.

A capacity-1 cache contains only the immediately previous target. It therefore misses on the first access and exactly when the target changes from the preceding access. Its miss count for that epoch is one plus the number of adjacent target changes.

An unbounded associative fresh-handle cache misses exactly on the first occurrence of each distinct target identity in that epoch. Its miss count is therefore the number of distinct targets in the epoch.

Every first occurrence counted by the unbounded cache is necessarily also a one-handle miss, so `M_inf <= M_1` after summing independently over all epochs. The saving `S = M_1 - M_inf` is thus nonnegative.

Equality fails exactly when the one-handle cache misses on a target that the unbounded cache has already seen in the same epoch. That event is precisely a **non-consecutive revisit**: target `A` is requested, at least one different target intervenes, and `A` is requested again before the freshness epoch changes. Hence strict saving exists iff at least one non-consecutive same-epoch revisit exists.

On every epoch change both caches are cleared. Numerical target equality across the boundary is insufficient: the old handle belongs to a different freshness generation. Consequently, cross-epoch revisits cannot contribute to `S`.

### Dimensional / unit check

`M_1`, `M_k`, `M_inf`, and `S` are counts and therefore dimensionless. If a later experiment measures a homogeneous per-grounding cost `c_g`, an estimated avoided cost would have the same unit as `c_g` after multiplying by the dimensionless count `S`. This study does **not** assign seconds or tokens to `c_g`, so it makes no latency/token-saving claim.

## Canonical controls

- `A,A,A`, one epoch: all cache sizes miss once; multi-handle retention adds nothing.
- `A,B,A,B`, one epoch: one handle misses 4 times; LRU-2 misses 2 times. This is the clean positive witness.
- `A,B,A`, epoch reset before final `A`: all tested caches miss 3 times. Same target name does not authorize stale reuse.
- `A,B,C,A`, one epoch: LRU-2 misses 4 times while LRU-3/unbounded misses 3. Capacity matters even when the general theorem predicts a possible revisit saving.
- `A,A,A` with a new epoch before every access: unbounded cache misses 3 times. Repeated numeric/semantic identity does not cross currentness generations.

## Interpretation

#1643 and #1654 ruled out two superficial explanations: extra logical cursors do not create independent actuator resources, and parked aliases do not erase single-pointer endpoint movement by themselves. #1682 identifies a different, valid mechanism:

> Multiple **fresh semantic target handles** can reduce repeated re-grounding only when the task revisits targets within the same validity epoch and the cache is large enough to retain them.

The mechanism is a freshness-scoped associative cache, not the visible cursor count. A UI could expose this as multiple cursors, but the minimum sufficient runtime primitive is closer to multiple current target handles / anchors with explicit invalidation.

This also explains the token-saving hypothesis precisely: savings are possible only if a cache miss would otherwise trigger a model-visible grounding boundary, and only after subtracting validation/cache-management cost. Neither condition is measured here.

## Next discriminator

The next high-information experiment should hold task/model/interface semantics fixed and vary only target-handle retention capacity on a private repeated-target GUI trace:

1. capture exact current target handles with surface/binding generation;
2. compare capacity 1 vs capacity 2 on an `A-B-A-B`-like task family;
3. inject a generation change control that must force both arms to re-ground;
4. separately measure model boundaries/tokens attributable to target grounding and local validation cost;
5. require identical task correctness and zero stale-handle admissions.

Do not combine this with independent-pointer concurrency or warp latency; those are already separate mechanisms.

## Scope limits

This is exact discrete cache/currentness semantics. It does not prove automatic target-identity resolution, target geometry stability, model/token savings, wall-clock benefit, human tempo, GUI correctness, or production runtime suitability. Finite-cache counts shown here use LRU; the unbounded theorem is policy-independent.
