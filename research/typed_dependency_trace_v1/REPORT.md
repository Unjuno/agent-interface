# Typed dependency trace discovery v1

Status: **RETAIN typed dependency classes as a mechanism candidate; HOLD automatic dependency discovery as solved.**

Immutable repository base: `7f42fd577dff98d6a27a8eceb79d86bee0358bf9`.

This is a development/discovery block under Issues #104, #165, and #93. It does not modify shared runtime, formal Doom allocations, preregistrations, or historical results.

## Question

Can a compiled/local method discover a dependency footprint by tracing what it reads, while avoiding both stale continuation from missing dependencies and unnecessary stops from over-broad dependencies?

The block increases complexity one factor at a time:

1. ordinary branch/control reads;
2. alias resolution identity;
3. query/range membership (phantom insertion);
4. maintenance atomicity of a query epoch.

## Environment

- Linux 6.18.44 x86_64, glibc 2.41
- CPython 3.13.5
- Git 2.47.3
- reported CPU: Intel Xeon Platinum 8573C, 5 visible CPUs
- sampled median `/proc/cpuinfo` clock approximately 2300 MHz; frequency not pinned
- batch 1, one process driving local temporary repositories

Timing is descriptive only. Repeated deterministic states are mechanism repetitions, not independent application samples.

## Rung 1 — ordinary control/data reads

Minimal program: `if mode == 0: use A else: use B`. Plan state is `mode=0, A=0, B=0`.

Three footprint strategies were compared for 500 repetitions of each condition:

- `data_only`: records `A` but omits the control predicate `mode`;
- `full_dynamic`: records every value actually read, including `mode` and active `A`;
- `static_union`: records `mode`, `A`, and inactive `B`.

| mutation | data_only | full_dynamic | static_union |
|---|---:|---:|---:|
| stable | correct 500/500 | correct 500/500 | correct 500/500 |
| control `mode` changes | **stale commit 500/500** | correct reject 500/500 | correct reject 500/500 |
| active `A` changes | correct reject 500/500 | correct reject 500/500 | correct reject 500/500 |
| inactive `B` changes | correct continue 500/500 | correct continue 500/500 | **false reject 500/500** |

**Finding:** in this simple branch, dynamic tracing is exact only if control-predicate reads are dependencies. Static union is safe here but unnecessarily blocks changes to the inactive branch.

## Rung 2 — alias resolution is itself a dependency

Real Git symbolic ref fixture. Logical `refs/meta/target` initially resolves to `refs/heads/a`; both `a` and `b` initially contain the same OID A. The planned effect changes the planned logical target from OID A to OID B.

Compared:

- `oid_only`: record only the dereferenced OID and later CAS the logical symbolic ref;
- `path_plus_oid`: record the observed symbolic-ref target path plus OID, and atomically verify the path while updating the planned concrete ref.

100 repetitions per cell:

| mutation | oid_only | path_plus_oid |
|---|---:|---:|
| stable | correct 100/100 | correct 100/100 |
| concrete `a` OID changes | reject 100/100 | reject 100/100 |
| alias remaps `a -> b`, same OID A | **wrong commit to b 100/100** | **reject 100/100** |
| unrelated ref changes | continue 100/100 | continue 100/100 |

Median measured commit section was approximately 4.1–4.8 ms across these cells. The mechanism result, not the small timing difference, is the point.

**Finding:** value/version tracing alone is insufficient when resource identity is resolved through an alias. Resolution provenance must be represented as a dependency when semantic identity depends on it.

## Rung 3 — point reads miss query phantoms

Real Git ref namespace fixture. At plan time `refs/candidates/` contains `b` and `c`; the planner chooses lexicographically first `b`. A new `refs/candidates/a` inserted after planning changes the correct query result without changing `b`.

Compared:

- `point_only`: verify only selected `b` OID;
- `namespace_epoch`: also verify a candidate-namespace epoch;
- `global_epoch`: verify an epoch bumped by any ref mutation.

The first 100-repetition attempt exceeded the execution envelope and is excluded from claims. A new frozen 20-repetition-per-cell block completed: 240 rows.

| mutation | point_only | namespace_epoch | global_epoch |
|---|---:|---:|---:|
| stable | correct 20/20 | correct 20/20 | correct 20/20 |
| selected `b` changes | reject 20/20 | reject 20/20 | reject 20/20 |
| new higher-priority `candidates/a` | **stale commit 20/20** | reject 20/20 | reject 20/20 |
| unrelated namespace insertion | continue 20/20 | continue 20/20 | **false reject 20/20** |

Median plan/query collection cost in this fixture was roughly 17–21 ms; median commit/verify section roughly 4.1–5.2 ms. These are local Git/Python measurements, not product latency claims.

**Finding:** selection queries require a predicate/range dependency, not merely dependencies on rows/items returned by the query. A global epoch prevents phantoms but over-declares unrelated state.

## Rung 4 — query version metadata must be maintained atomically

The namespace epoch only works if every membership mutation updates it consistently.

### Missing epoch maintenance

Insert `candidates/a` without bumping the candidate epoch:

- point-only: stale commit 20/20;
- namespace epoch: **stale commit 20/20**.

### Non-atomic versus atomic writer maintenance

A writer that first inserts `candidates/a` and only later bumps the epoch exposes an intermediate window. The reader commits during that window:

- non-atomic insert then epoch bump: **stale commit 20/20**;
- one Git transaction that creates `candidates/a` and changes the epoch together: reader rejects 20/20.

**Finding:** a query epoch is not just observation metadata. Its maintenance must share the mutation's atomic visibility boundary, or the epoch itself has a time-of-check gap.

## Candidate dependency vocabulary

The smallest candidate suggested by these rungs is typed rather than a flat resource set:

- `READ(resource, version)` for ordinary data and control reads;
- `RESOLVE(alias, concrete_identity)` when logical identity is resolved indirectly;
- `QUERY(scope, predicate_version)` for membership/range selection;
- `WRITE(resource)` for the non-partial effect set.

All are plan-bound. Refreshing only a dependency token under an old action remains invalid per the prior Git provenance experiment.

## H / T / D / C / U

**H.** A typed dynamic trace can be more precise than static-union dependencies while remaining complete for the operation classes it explicitly observes.

**T.** 6,000 synthetic branch checks + 800 real-Git alias rows + 240 retained real-Git phantom rows + 40 missing-epoch rows + 40 writer-atomicity rows = **7,120 retained scored checks**. Deterministic repetitions test mechanism consistency, not population reliability.

**D.** RETAIN the typed vocabulary as a candidate. FAIL flat value-only tracing on alias remap and point-only tracing on phantom insertion. FAIL namespace epochs whose writers do not update them atomically. HOLD automatic footprint discovery because unobserved semantic assumptions and general GUI acquisition are not solved.

**C.** Static analysis may recover dependencies that a single dynamic execution does not observe, while over-broad static unions can reduce concurrency. Application-provided canonical identity or query epochs can make some dependencies explicit; arbitrary GUI surfaces may not expose them.

**U.** Development-known fixtures; no planner/model dependency authoring; no natural workload distribution; no GUI screenshot path in this block; no claim that Git-style epochs exist for arbitrary applications. Timing includes local Git process startup and host scheduling with unpinned clocks.

## Error check

The expected failure pattern is internally discriminating:

- omitting only control dependency breaks only the control-change case;
- omitting alias resolution breaks only same-value alias remap;
- omitting query predicate dependency breaks only phantom insertion;
- broad global predicate catches the phantom but blocks unrelated mutation;
- correct query epoch still fails when writer maintenance is absent/non-atomic.

This pattern is inconsistent with a single blanket 'reject on any change' implementation and separates dependency kinds by counterexample.

## Next smallest experiment

Do not add another global epoch. Test **static + dynamic footprint composition** on a tiny method with one untaken branch: can static analysis contribute a bounded *potential* dependency set while runtime tracing narrows it without losing the control/query dependencies demonstrated here? Measure false negatives and false positives against a finite ground-truth dependency graph before involving a frontier model.