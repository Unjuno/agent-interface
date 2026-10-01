# Staged dependency acquisition v1

Status: **RETAIN staged dependency acquisition only with plan-bound branch-selection validity at the selected-action boundary; RETAIN proof-backed v1 mutual-exclusion simplification and direct paired batching calibration; HOLD runtime ABI and live promotion.**

Immutable research base: `e94af964f85da1cbd4e2db0fd7840bfd8362c3ba`.

This is a bottom-up successor to Issues #104/#165 and draft PR #182. The exact Chromium-v5 live successor in #184 is SETUP_BLOCKED in the current container because the frozen Windows/WSL model-runner environment is absent; no substitute live benchmark is relabeled as v5.

## Question

If one compiled state has multiple possible action branches, should the runtime acquire the union of every branch's semantic/admission dependencies before branch selection, or acquire branch-selection dependencies first and only then obtain dependencies of the selected action?

The dependency vocabulary and fail-closed rules from prior blocks are unchanged. This block changes only when already-required dependencies are acquired and what semantic control condition must remain valid at final admission.

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

This first block established that inactive-branch union can be over-broad and interface-only scoping is incomplete. It did **not** yet model a state change between branch selection and selected-action acquisition; later rungs correct that assumption.

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

**Correction to Rung 1:** plain staging is unsafe across an inter-phase state change. Branch selection is plan-bound evidence.

## Rung 7 — SQLite atomic check+effect confirms the boundary

A file-backed SQLite fixture uses a state table and effect table. Phase 1 reads `mode=A`; one mutation occurs before phase 2; phase 2 performs validation and effect in one `BEGIN IMMEDIATE` transaction. Five mutation cases × three methods × 100 repetitions = 1,500 rows.

- staged without branch revalidation: mode flip produced wrong effect **100/100**;
- union: inactive `gB` invalidation produced false rejection **100/100**;
- staged + branch revalidation: all five cases correct **500/500**.

Descriptive phase-2 medians: union 20.184 us, staged+revalidation 21.440 us, naive staged 22.940 us. These are not product latency claims.

## Rung 8 — existing compiled-method shape integration

The mechanism was checked against the state-machine shape already used by `compiled_runtime_cross_domain_compat_v1` continuous control. Plan-time LEFT/RIGHT selects one movement action; current zone/surface/left-guard/right-guard/nuisance combinations were exhaustively enumerated: **96 states**.

- state union: stale 0, false reject **4**;
- staged without branch revalidation: stale **40**, false reject 0;
- staged + branch revalidation: **stale 0 / false reject 0**.

This is an existing compiled-method shape, not execution of the exact runtime module.

## Rung 9 — semantic predicate truth beats exact raw equality

For a single selected branch condition `x >= 0`, initial `x=-3..3`, current `x=-5..5`, guard false/true: **154 states**.

- no branch revalidation: **38 stale executes**;
- exact raw `x` equality: 0 stale but **32 false rejects**;
- predicate-truth equality: **stale 0 / false reject 0**.

Thus branch validity should preserve the authored semantic condition rather than exact raw state unless exact identity/version is itself part of the contract.

## Rung 10 — selected-predicate truth is not enough when another branch can become true

The previous rung considered one selected branch in isolation. The runtime, however, requires exactly one matching branch.

### Independent branch predicates

A:`x >= 0`, B:`y >= 0`; initial states contain exactly one match. Initial `x,y in [-3,3]`, final `x,y in [-5,5]`: **2,904 transitions**.

| revalidation | stale accepts | false rejects | correct |
|---|---:|---:|---:|
| selected branch predicate remains true | **864** | 0 | 2,040 |
| exact raw `x,y` equality | 0 | **696** | 2,208 |
| **same branch remains unique match** | **0** | **0** | **2,904** |

The 864 stale cases arise when the selected branch stays true but the competing branch becomes newly true; a fresh runtime selection would be ambiguous and must not execute.

### Overlapping conditions on one variable

A:`x >= 0`, B:`x <= 2`, 66 transitions from initially unique states:

- selected-truth: **18 stale accepts**;
- exact raw equality: **18 false rejects**;
- unique-selection: **66/66 exact**.

Therefore the general plan-bound control dependency is semantic branch-selection identity:

`BRANCH_SELECTION(state, selected_branch, unique=true)`.

## Rung 11 — v1 equality branches admit an exact mutual-exclusion certificate

`compiled-gui-interface-v1` branch `when` clauses are conjunctions of scalar equalities represented as partial maps. Two branches are mutually exclusive iff some shared predicate is assigned different expected values.

**Proof.** A conflicting shared equality makes joint satisfaction impossible. Conversely, without any conflict the union of both partial maps is consistent; assigning every mentioned predicate its demanded value satisfies both branches. Therefore the criterion is necessary and sufficient for the v1 branch language.

Implementation audit: 100,000 generated branch pairs over four ternary predicates compared to exhaustive assignment enumeration:

- mismatches: **0 / 100,000**;
- certified mutually exclusive: 68,750;
- overlapping: 31,250.

Retained compiled fixture shapes checked:

- XTerm v4: 5/5 branch pairs certified;
- MAP01 composition: 3/3;
- continuous control: 6/6;
- desktop two-step: 5/5;
- Chromium v5: one branch/state, so no competing pair.

Thus v1 can lower the general `BRANCH_SELECTION` dependency to the selected branch's complete `when` condition **only when all competing branches are independently certified mutually exclusive**. Richer predicate languages require a different proof system or full unique-selection recomputation.

## Architecture consequence

Separate five questions:

1. **Dependency correctness:** what evidence is semantically required? Typed and fail-closed.
2. **Plan-bound decision validity:** by default preserve unique branch-selection identity; proof-backed mutually exclusive v1 states may revalidate only the selected `when` condition.
3. **Selected-action acquisition staging:** after branch selection, acquire only selected-action dependencies rather than inactive-branch dependencies.
4. **Final admission boundary:** validate branch-selection/selected action evidence coherently with effect authority.
5. **Physical batching:** one union request versus multiple staged requests is backend-specific and must not alter semantic membership.

Candidate boundary:

`branch/pending observation -> choose candidate action -> acquire selected action dependencies -> revalidate BRANCH_SELECTION (or proof-backed selected when) + selected action dependencies -> admit/execute`

Hidden admission/verifier dependencies remain mandatory. Inactive branch action dependencies are not.

## H / T / D / C / U

**H.** Staging can remove inactive-branch false stops only if final admission preserves the plan-bound decision result and selected-action dependencies; v1 equality states with a retained mutual-exclusion certificate can safely use a cheaper selected-branch recheck.

**T.** 100,000 dependency-membership trials; normalized cost sweep; heavy-hash and SQLite microbenchmarks; retained failed linear calibration; paired calibration with 5,000-repetition holdouts; 100,000 inter-phase mutation trials; 1,500 SQLite atomic rows; 96 compiled-shape states; 154 single-predicate states; 3,047 branch-uniqueness transitions; 100,000 generated certificate pairs; 19 retained multi-branch fixture pairs.

**D.** RETAIN staged acquisition only with plan-bound decision revalidation. FAIL naive staged. RETAIN `BRANCH_SELECTION(state, selected_branch, unique=true)` as the general control dependency. RETAIN proof-backed selected-`when` simplification for mutually exclusive v1 equality branches. RETAIN direct paired batching calibration only as backend-specific scheduling evidence. HOLD exact-runtime/live promotion.

**C.** Generated fixtures know ground truth. Richer predicates, hidden application invariants, or undeclared verifier/admission state can invalidate static simplifications. A real application may not expose branch and selected-action evidence under one authoritative final boundary.

**U.** Exact `compiled_gui_interface_v1.py` execution remains SETUP_BLOCKED in the current container under Issue #197. No Chromium-v5 live replication, model calls, network backend, GPU, or production-load calibration.

## Error check

The failure modes discriminate the mechanisms:

- omit hidden action dependencies -> stale accepts;
- union inactive action dependencies -> false rejects;
- stage without revalidating control decision -> stale execution after branch change;
- selected predicate truth without uniqueness -> stale execution when a competitor becomes true;
- exact raw equality -> avoidable false rejects;
- unique branch-selection revalidation -> zero seeded errors in overlapping branch fixtures;
- proof-backed v1 mutual exclusivity -> selected `when` revalidation is equivalent to unique selection in the stated language.

This pattern is inconsistent with blanket reject-on-any-change and blind continuation.

## Next smallest experiment

Execute Issue #197 with byte-exact `compiled_gui_interface_v1.py`. Prefer a state with at least two branches and retain a static mutual-exclusivity certificate when available. Compare the general unique-selection check with the proof-backed selected-`when` simplification while keeping selected-action dependencies, canonical evidence identity, authority/release semantics, batching calibration, and model/live concerns fixed.
