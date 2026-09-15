# Staged dependency acquisition v1

Status: **RETAIN staged dependency acquisition only with plan-bound branch revalidation at the selected-action boundary; RETAIN direct paired plan calibration as a scheduling candidate; HOLD runtime ABI and live promotion.**

Immutable research base: `e94af964f85da1cbd4e2db0fd7840bfd8362c3ba`.

This is a bottom-up successor to Issues #104/#165 and draft PR #182. The exact Chromium-v5 live successor in #184 is SETUP_BLOCKED in the current container because the frozen Windows/WSL model-runner environment is absent; no substitute live benchmark is relabeled as v5.

## Question

If one compiled state has multiple possible action branches, should the runtime acquire the union of every branch's semantic/admission dependencies before branch selection, or acquire branch-selection dependencies first and only then obtain dependencies of the selected action?

The dependency vocabulary and fail-closed rules from prior blocks are unchanged. This block changes only **when** already-required dependencies are acquired and revalidated.

## Rung 1 — dependency membership and inactive-branch precision

100,000 deterministic generated trials contain one branch-control dependency, optional pending-effect/verifier dependencies, two possible action branches A/B, branch-specific symbol dependencies, hidden admission dependencies, and one relevant/inactive/unrelated mutation.

Compared:

1. `state_union`: branch/pending plus both A and B action dependencies;
2. `staged`: branch/pending first, then selected action symbol/admission dependencies;
3. `planner_only`: branch/pending plus selected visible symbol dependencies, omitting hidden admission/verifier dependencies.

| mode | stale accepts | false rejects | median dependency count |
|---|---:|---:|---:|
| state_union | 0 | **33,238** | 10 |
| staged | 0 | 0 | 6 |
| planner_only | **14,147** | 0 | 4 |

This first block established that inactive-branch union can be over-broad and interface-only scoping is incomplete. It did **not** yet model a state change between branch selection and selected-action acquisition; Rung 6 corrects that assumption.

## Rung 2 — batching cost is separate from semantic correctness

A normalized sweep varies only the fixed cost of the second request. In the same generated dependency-size distribution:

- fixed cost <= 1 dependency-unit: staged wins 100%;
- fixed cost = 2: staged wins 83,310/100,000, ties 16,690;
- fixed cost = 4: union wins 50,161/100,000, staged wins 16,576, ties 33,263;
- fixed cost >= 8: union wins 100%.

This is a cost-model result, not a product benchmark.

## Rung 3 — two executable backend examples

Representative shape: branch/pending 2 dependencies, selected action 4, inactive branch 4. Linux 6.18.44 x86_64, CPython 3.13.5, SQLite 3.46.1, batch 1, CPU frequency not pinned.

### Heavy local predicate backend

Each dependency performs SHA-256 work over a deterministic 16-KiB payload.

- union (10 deps): median **117.640 us**, p95 254.736 us;
- staged (2 + 4): median **70.674 us**, p95 139.474 us;
- staged median improvement: about **39.9%**.

### Light SQLite scalar backend

- union: median **10.343 us**, p95 14.776 us;
- staged: median **10.620 us**, p95 14.495 us;
- union median advantage: about **2.7%**.

The same semantic dependency graph can prefer opposite batching schedules depending on its producer/backend.

## Rung 4 — a simple linear cost model failed

A `fixed request cost + per-dependency cost` fit from 1/2/4/8/10-dependency medians:

- heavy backend: predicted staged, actual staged;
- SQLite backend: predicted staged, actual **union**.

The failed model is retained instead of tuning it after seeing the answer.

## Rung 5 — direct paired plan calibration

Directly benchmark the two legal plans for the actual shape/backend and choose the lower median.

5,000-repetition holdout:

- heavy: staged **70.907 us** vs union 117.799 us -> staged;
- SQLite: union **10.222 us** vs staged 10.746 us -> union.

For calibration budgets 10/20/50/100/200/500 repetitions per plan, 20 independent blocks per budget chose the holdout winner 20/20 for both tested backends. This is environment-specific evidence, not a universal stability guarantee.

## Rung 6 — branch-validity TOCTOU breaks naive staging

The first staged block assumed the branch remained valid between phase 1 and phase 2. A successor explicitly mutates state after branch selection and before selected-action dependency acquisition. 100,000 trials compare:

- `union_phase2`: revalidate branch plus selected and inactive action guards;
- `staged_no_branch_revalidate`: read only selected guard in phase 2;
- `staged_revalidate`: revalidate branch predicate plus selected guard in phase 2.

| method | stale executes | false rejects | median phase-2 dependencies |
|---|---:|---:|---:|
| union_phase2 | 0 | **20,084** | 3 |
| staged_no_branch_revalidate | **19,926** | 0 | 1 |
| staged_revalidate | **0** | **0** | 2 |

**Correction to Rung 1:** plain staging is unsafe across an inter-phase state change. Branch selection is itself plan-bound evidence. The predicate that selected the action must still hold at final selected-action admission, or be protected by an equivalent snapshot/version capability.

## Rung 7 — SQLite atomic check+effect confirms the boundary

A file-backed SQLite fixture uses a state table and effect table. Phase 1 reads `mode=A`; one mutation occurs before phase 2; phase 2 performs validation and effect in one `BEGIN IMMEDIATE` transaction. Five mutation cases × three methods × 100 repetitions = 1,500 rows.

- staged without branch revalidation: mode flip produced wrong effect **100/100**;
- union: inactive `gB` invalidation produced false rejection **100/100**;
- staged + branch revalidation: all five cases correct **500/500**.

Descriptive phase-2 medians: union 20.184 us, staged+revalidation 21.440 us, naive staged 22.940 us. These are not product latency claims.

## Architecture consequence

Separate four questions:

1. **Dependency correctness:** what evidence is semantically required? Typed and fail-closed.
2. **Plan-bound branch evidence:** the branch predicate used to select an action must be revalidated at the selected-action admission boundary.
3. **Acquisition staging:** after branch selection, acquire only selected-action dependencies rather than inactive-branch dependencies.
4. **Batching policy:** whether branch+action dependencies are physically fetched in one request or multiple requests is backend-specific and must not change semantic membership/revalidation.

Candidate boundary:

`branch/pending observation -> choose candidate action -> acquire selected action dependencies -> atomically/freshly revalidate branch predicate + selected action dependencies -> admit/execute`

Hidden admission/verifier dependencies remain mandatory. Inactive branch dependencies are not.

## H / T / D / C / U

**H.** Staging can remove inactive-branch false stops only if the plan-bound branch predicate is revalidated together with selected-action dependencies at final admission; batching can then be optimized independently.

**T.** 100,000 dependency-membership trials; normalized cost sweep; heavy-hash and SQLite microbenchmarks; retained failed linear calibration; direct paired calibration with 5,000-repetition holdouts; 100,000 inter-phase mutation trials; 1,500 SQLite atomic validation/effect rows.

**D.** PASS only for **staged + branch-predicate revalidation**: stale 0 / false reject 0 in the 100,000-trial inter-phase block and 500/500 correct SQLite cases. Plain staged FAILS (19,926/100,000 stale executes; SQLite mode-flip wrong 100/100). State union remains sound but over-broad (20,084/100,000 false rejects; SQLite inactive-guard false reject 100/100). RETAIN direct paired batching calibration only as a backend-specific scheduling candidate. HOLD generic runtime/live promotion.

**C.** Generated graphs know their ground-truth dependencies; discovery remains a separate problem. A real application may not expose branch predicate and action dependencies under one atomic/fresh boundary. Calibration may drift with load or have too-small performance margins.

**U.** No Chromium-v5 live replication, no model calls, no network backend/GPU, unpinned CPU frequency, synthetic heavy workload, local SQLite. Natural workload frequencies and production scheduling noise are unknown.

## Error check

The failure modes discriminate the mechanisms:

- omit hidden action dependencies -> stale accepts;
- union inactive action dependencies -> false rejects;
- stage without revalidating the selecting branch -> stale executes after mode flip;
- stage and revalidate branch + selected action -> zero seeded correctness errors.

This pattern is inconsistent with blanket reject-on-any-change and with blind continuation.

## Next smallest experiment

Integrate only **staging + branch-predicate revalidation**, not cost calibration, into one existing compiled finite fixture with two action branches and disjoint admission dependencies. Keep canonical evidence identity and existing authority semantics unchanged. Test stable, selected-dependency change, inactive-dependency change, branch flip, and unrelated change separately.
