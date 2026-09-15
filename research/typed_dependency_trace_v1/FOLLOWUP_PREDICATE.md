# Follow-up — semantic predicate dependencies and transactional query checks

This follow-up adds one refinement to `REPORT.md`: dependency validity should sometimes bind the **semantic predicate result**, not exact raw resource version equality.

## Rung 5 — control predicate truth versus exact version

A finite typed-DSL state space used four methods (`branch`, `alias`, `query`, `combo`), two initial control states, and eight single mutations = 64 cases.

The typed trace from the first report recorded exact `READ(mode, version)`. It was sound but produced 2/64 false rejects: when `mode` changed from nonzero value 1 to nonzero value 2, the branch result and planned effect were unchanged, but exact-version validation rejected.

Replacing only the control dependency with `PRED_EQ(mode, 0, observed_truth)` produced:

- **64/64 correct**;
- stale accepts: 0;
- false rejects: 0.

Value-only tracing in the same finite set remained incomplete: 9/64 stale accepts from alias/query/control omissions plus 2/64 false rejects.

**Interpretation:** dependency precision can be semantic. For control flow, exact value/version equality may be stricter than needed; the validity condition is often preservation of the predicate that selected the plan branch.

## Rung 6 — query-result predicate versus whole-namespace epoch

Minimal selection semantics: `selected = min(candidates)`, initial set `{b,c}`. 500 repetitions per mutation.

| mutation | namespace epoch | query-result predicate `min == b` |
|---|---:|---:|
| none | correct 500/500 | correct 500/500 |
| insert `a` | reject 500/500 | reject 500/500 |
| insert `z` | **false reject 500/500** | correct continue 500/500 |
| delete `c` | **false reject 500/500** | correct continue 500/500 |
| delete `b` | reject 500/500 | reject 500/500 |

Thus a namespace epoch is complete but can still be unnecessarily broad relative to the actual query predicate.

## Rung 7 — real transactional enforcement in SQLite

SQLite 3.46.1 in-memory databases were used to implement the same `MIN(name)` dependency inside one `BEGIN IMMEDIATE` transaction. Compared:

- collection epoch check;
- recompute `SELECT MIN(name)` and require it to equal the planned result before writing the effect.

100 repetitions per mutation per method = 1,000 rows.

Results:

- predicate transaction: **500/500 correct**, stale 0, false reject 0;
- epoch transaction: safe on relevant changes, but **200/200 false rejects** for irrelevant `insert z` and `delete c` changes.

Median effect/reject transaction sections were approximately 0.004–0.011 ms in this in-memory fixture; these are not product latency measurements.

### Concurrency/linearization check

20 repetitions per ordering used two SQLite connections against a file-backed WAL database.

- effect transaction acquires `BEGIN IMMEDIATE` first, checks `MIN=b`, then competitor attempts `insert a`: effect commits first 20/20; competitor acquires the write lock afterward 20/20; competitor wait median **8.312 ms**; final state contains `a`, but the effect is correctly linearized before it.
- competitor commits `insert a` first: predicate transaction observes `MIN=a` and emits no effect 20/20.

This closes the check/effect race for the tested cooperative transaction boundary.

## Rung 8 — completeness requires mediated reads

A typed tracer cannot record dependencies that method code bypasses.

500 repetitions changed hidden `guard` after planning:

- method reads `A` through the typed API but directly accesses raw `guard`: **stale accept 500/500**;
- same method reads both `A` and `guard` through the typed API: reject 500/500, stale 0.

A separate instrumentation benchmark used typed `read / resolve / query` operations:

- known branch footprint exact: 10,000/10,000;
- alias footprint exact: 10,000/10,000;
- query footprint exact: 10,000/10,000.

A value-only tracer matched the 10,000 branch cases but matched 0/10,000 alias and 0/10,000 query typed footprints because it omitted the resolution/query dependency class.

Local CPython microbenchmark, 30 batches × 20,000 calls, batch 1:

| method | raw median/call | typed trace median/call | median added time |
|---|---:|---:|---:|
| branch | 159 ns | 461 ns | 302 ns |
| alias | 132 ns | 440 ns | 307 ns |
| query | 129 ns | 475 ns | 346 ns |

These are interpreter-local measurements and do not include application I/O, model calls, IPC, or commit validation.

## Updated candidate

The evidence now suggests a more precise vocabulary:

- `READ(resource, version)` for exact-value dependencies;
- `PREDICATE(expression, observed_truth/result)` when branch/query validity is semantic rather than raw-version equality;
- `RESOLVE(alias, canonical_identity)` for resolution provenance;
- `QUERY(scope, semantic_predicate)` when the effect owner can atomically re-evaluate it;
- `WRITE(set)` for the non-partial effect set.

The producer must mediate all semantic reads; bypassable raw state invalidates completeness. The effect owner must atomically validate predicates with the mutation, or the predicate check regresses to TOCTOU.

## Decision

**RETAIN** typed/semantic dependency tracing as a research candidate.

**HOLD** automatic GUI dependency discovery and unrestricted Python instrumentation. The current positive result assumes a cooperative typed access surface or transaction-capable application boundary.

## Next smallest question

Can a compiled method expose a **capability-limited dependency API** so all semantic reads are mediated, while raw screenshots remain observational evidence rather than an untracked semantic backchannel? Test one existing compiled method before designing a general public ABI.