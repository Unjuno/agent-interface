# Follow-up — exact mutual-exclusion certificate for v1 equality branches

Status: **RETAIN as a proof-backed optimization of branch-selection revalidation.**

## Why this follows the uniqueness counterexample

The preceding block showed that `selected branch predicate remains true` is unsafe when a competing branch can become newly true. General final admission therefore needs to preserve the same unique branch-selection result.

However, `compiled-gui-interface-v1` branch conditions are conjunctions of scalar equalities represented as maps `predicate -> expected value`. For this restricted language, mutual exclusion is decidable exactly without a solver.

## Criterion

Two branch condition maps A and B are mutually exclusive iff there exists at least one shared predicate `p` such that `A[p] != B[p]`.

### Proof

If such a conflicting shared predicate exists, no observation can satisfy both equalities simultaneously, so the branches cannot both match.

Conversely, if no shared predicate conflicts, the union of the two partial maps is consistent. Assign every mentioned predicate the value demanded by that union; all other predicates are arbitrary. That observation satisfies both branches. Therefore the branches overlap.

Thus the criterion is necessary and sufficient for the v1 equality-conjunction language.

## Finite implementation check

100,000 generated branch pairs over four predicates with ternary domains were compared against exhaustive assignment enumeration:

- certificate mismatches: **0 / 100,000**;
- certified mutually exclusive: 68,750;
- overlapping: 31,250.

The finite check is not the proof; it audits the implementation of the criterion.

## Existing compiled-spec shapes

Applying the criterion to retained branch maps used by existing compiled research fixtures:

| spec | multi-branch pairs | certified exclusive |
|---|---:|---:|
| Chromium v5 | 0 | 0 (single branch/state) |
| XTerm v4 | 5 | **5** |
| MAP01 composition | 3 | **3** |
| continuous control | 6 | **6** |
| desktop two-step | 5 | **5** |

All 19 existing multi-branch pairs checked here are statically mutually exclusive under the v1 branch language.

## Architecture consequence

Default correctness dependency remains semantic branch-selection identity:

`BRANCH_SELECTION(state, selected_branch, unique=true)`.

But v1 can compile a cheaper proof-backed form:

1. statically check every competitor against the selected branch for an equality conflict;
2. if all competitors are certified mutually exclusive, final admission only needs to revalidate the selected branch's complete `when` condition;
3. otherwise, final admission must recompute/revalidate branch-selection uniqueness across the competing set.

This is a semantic optimization, not a measured runtime speedup.

## H / T / D / C / U

**H.** The restricted v1 equality-conjunction language admits an exact static mutual-exclusion certificate that can safely simplify unique-selection revalidation.

**T.** Formal criterion + 100,000 generated-pair implementation audit + 19 retained multi-branch pairs from existing compiled fixture shapes.

**D.** PASS for the criterion in the stated language. RETAIN proof-backed simplification. Do not generalize to inequalities, disjunctions, aliases, queries, or arbitrary predicates.

**C.** Later interface versions with richer predicates will need a different proof system or explicit branch-selection recomputation.

**U.** Existing fixture branch maps were transcribed from retained repository sources; exact-runtime execution remains blocked in the current container under Issue #197.

## Next gate

Issue #197 should record whether the chosen exact-runtime fixture's state receives this static certificate. If certified, compare the proof-backed selected-`when` recheck against full unique-selection recomputation for identical correctness; if not certified, use full selection identity.
