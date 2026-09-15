# Staged dependency acquisition v1

Status: **RETAIN staged dependency acquisition as a correctness/precision candidate; RETAIN direct paired plan calibration as a scheduling candidate; HOLD runtime ABI and live promotion.**

This is a bottom-up successor to Issues #104/#165 and draft PR #182. The exact Chromium-v5 live successor in #184 is SETUP_BLOCKED in the current container because the frozen Windows/WSL model-runner environment is absent; no substitute live benchmark is relabeled as v5.

## Question

If one compiled state has multiple possible action branches, should the runtime acquire the union of every branch's semantic/admission dependencies before branch selection, or acquire branch-selection dependencies first and only then obtain dependencies of the selected action?

The intervention is scheduling only. The required dependency vocabulary and fail-closed rules from prior blocks are unchanged.

## Rung 1 — correctness and precision

100,000 deterministic generated trials. Each trial contains:

- one branch-control dependency;
- optional pending-effect and verifier dependencies;
- two possible action branches A/B;
- branch-specific symbol dependencies;
- branch-specific hidden admission dependencies;
- one seeded change classified as relevant, inactive-branch, or unrelated.

Compared:

1. `state_union`: branch/pending dependencies plus both A and B action dependencies;
2. `staged`: branch/pending dependencies, then only the selected action's symbol/admission dependencies;
3. `planner_only`: branch/pending plus selected visible symbol dependencies, omitting hidden admission/verifier dependencies.

| mode | stale accepts | false rejects | median dependency count |
|---|---:|---:|---:|
| state_union | 0 | **33,238** | 10 |
| staged | **0** | **0** | 6 |
| planner_only | **14,147** | 0 | 4 |

Thus a one-shot state union is sound but can be unnecessarily broad, while interface-only scoping remains incomplete. Staging branch selection before action-specific acquisition preserves the generated ground truth exactly in this fixture.

## Rung 2 — correctness does not determine batching cost

A normalized cost sweep treats one dependency's work as one unit and varies the fixed cost of an extra request. In the same generated dependency-size distribution:

- fixed cost <= 1 dependency-unit: staged wins 100% of trials;
- fixed cost = 2: staged wins 83,310/100,000, ties 16,690;
- fixed cost = 4: union wins 50,161/100,000, staged wins 16,576, ties 33,263;
- fixed cost >= 8: union wins 100%.

A static hybrid that chooses staged only when avoided inactive work exceeds the extra request cost equals the cheaper candidate for every generated case. This is a cost-model result, not a product benchmark.

## Rung 3 — two executable backend examples

Representative shape: branch/pending acquisition 2 dependencies, selected action 4, inactive branch 4.

Environment: Linux 6.18.44 x86_64, CPython 3.13.5, SQLite 3.46.1, batch 1, CPU frequency not pinned.

### Heavy local predicate backend

Each dependency performs SHA-256 work over a deterministic 16-KiB payload.

- union, 10 dependencies: median **117.640 us**, p95 254.736 us;
- staged, 2 + 4 dependencies: median **70.674 us**, p95 139.474 us;
- staged median improvement: about **39.9%**.

### Light SQLite scalar backend

In-memory SQLite scalar reads, same logical dependency counts.

- union: median **10.343 us**, p95 14.776 us;
- staged two queries: median **10.620 us**, p95 14.495 us;
- union median advantage: about **2.7%**.

Therefore the same dependency graph can prefer opposite batching schedules depending on the producer/backend.

## Rung 4 — a simple linear cost model failed

A first calibration fit `request fixed cost + per-dependency cost` from 1/2/4/8/10-dependency medians.

- heavy backend: predicted staged, actual staged — correct;
- SQLite backend: predicted staged, actual union — **wrong**.

The SQLite cost curve is not sufficiently represented by the simple linear model for this close decision. This failed model is retained rather than tuned until success.

## Rung 5 — direct paired plan calibration

Instead of fitting a richer model, directly benchmark the two legal acquisition plans for the actual shape and backend, then choose the lower median.

Holdout (5,000 repetitions/plan):

- heavy: staged 70.907 us vs union 117.799 us -> staged;
- SQLite: union 10.222 us vs staged 10.746 us -> union.

Twenty independent calibration blocks were run for each calibration budget 10/20/50/100/200/500 repetitions. Even at **10 repetitions/plan**, all 20/20 heavy blocks chose staged and all 20/20 SQLite blocks chose union, matching the holdout winner in this environment.

This does not establish universal calibration stability; the tested margins were sufficient here.

## Architecture consequence

Separate three questions:

1. **Dependency correctness:** what evidence is required? This remains typed and fail-closed.
2. **Acquisition staging:** branch-control/pending evidence can be acquired before selected-action admission evidence, preventing inactive-branch over-declaration.
3. **Batching policy:** whether to perform one union request or two staged requests is backend-specific and should not be encoded as a semantic rule.

Candidate scheduler behavior:

- derive a safe `branch/pending` set and action-specific dependency sets;
- never omit hidden admission/verifier dependencies;
- allow a producer/backend to choose union vs staged batching without changing semantic dependency membership;
- prefer direct paired calibration over an assumed linear cost model until a better cost model is validated.

## H / T / D / C / U

**H.** Separating branch selection from selected-action dependency acquisition reduces inactive-branch false stops without creating stale accepts, while batching can be chosen independently per backend.

**T.** 100,000 generated correctness trials; 100,000-trial normalized cost sweeps; executable heavy-hash and SQLite microbenchmarks; failed linear calibration retained; direct paired calibration with 5,000-repetition holdouts and 20 blocks at six calibration budgets.

**D.** PASS at the generated mechanism level for staged dependency membership: stale 0, false reject 0. RETAIN direct paired batching calibration in the two tested backends. HOLD generic runtime integration/live speedup.

**C.** Generated dependency graphs know ground truth and do not solve dependency discovery itself. Two-stage acquisition can increase latency when request setup dominates. The direct calibration may be unstable for smaller performance margins or changing system load.

**U.** No Chromium-v5 live replication, no model calls, no network backend, no GPU, unpinned CPU frequency, synthetic heavy predicate workload, in-memory SQLite. Natural workload frequencies are unknown.

## Next smallest experiment

Integrate only the **staging boundary**, not the cost scheduler, into one existing compiled finite fixture with two action branches and disjoint admission dependencies. Verify that an inactive branch's dependency can change without causing a false stop, while a selected branch dependency change still fails closed. Keep canonical evidence identity and current runtime authority semantics unchanged.
