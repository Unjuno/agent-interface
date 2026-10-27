# Partial correspondence across GUI revisions

## Predecessor result: #8675

T0 A01 reports `PASS_RELATIONAL_REIDENTIFICATION_SCOPED` for a finite synthetic corpus. The candidate correctly re-identified 100/300 held-out positive cases (33.3%), 33.3 percentage points above both exact ID/path and exact role-label-actionability baselines. It observed zero false rebinds among 500 negatives (one-sided 95% upper bound 0.5974%). All 200 automorphism, 150 semantic-change, and 150 removed-target controls abstained. Recovery was limited to sibling reorder (100/100); all inserted-duplicate-target and transparent-wrapper cases abstained.

The method used exhaustive injective assignment with Gibbs-softened costs; it is not a canonical entropic Gromov-Wasserstein solver. The result grants no live target handle, freshness, action authority, task effect, or product behavior. Evidence is preserved in the [A01 artifact](../../research/analysis/cross_revision_target_transport_8675_t0_20261009/REPORT.md), originally proposed in [PR #8708](https://github.com/Unjuno/agent-interface/pull/8708), and [Issue #8675](https://github.com/Unjuno/agent-interface/issues/8675).

## Successor proposal: #8868

**Status:** Open, unverified algorithmic successor; no allocation result reported.

#8868 asks whether an explicit unmatched-node option can recover uniquely identifiable targets through benign insertions or wrappers without forcing ambiguous matches. It proposes a fresh additive corpus comparing:

- the frozen #8675 injective candidate as incumbent;
- exact ID/path and role-label-actionability baselines;
- bounded partial assignment/transport with explicit unmatched mass.

The successor freezes unmatched penalties, transported-mass range, abstention/concentration rule, and transformation-family held-outs. It includes benign insertions/wrappers, duplicate labels with and without unique neighborhoods, exact symmetric neighborhoods, deletion, semantic changes, stale/malformed graphs, and varied unmatched fractions. Low-confidence, non-unique, or unsupported cases must return AMBIGUOUS/NO_MATCH. Do not pool successor outcomes with #8675's corpus or adjust the predecessor's result. See [Issue #8868](https://github.com/Unjuno/agent-interface/issues/8868).

## Boundary

Graph correspondence is a proposal about structural continuity. It does not establish current GUI meaning, freshness, target authority, or effect. Any future partial matcher must remain behind the ordinary fresh-evidence and independent effect-verification contracts.
