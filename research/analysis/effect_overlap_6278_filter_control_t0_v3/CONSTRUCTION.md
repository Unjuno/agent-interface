# Construction record — allocation 03

Allocation `EFFECT-OVERLAP-6278-FILTER-CONTROL-T0-20261002-03` is a narrow successor to allocation 02's pre-candidate STOP. No allocation-02 frozen input or outcome is rewritten.

## Constructed discriminator

The four-route graph has the same task mix, routes, grants, fixed cost, per-use cost, capacity and dependency-loss scenarios in both arms. The sole arm difference is whether the `p_bc` route's advertised B coverage is accepted without edge truth (`declared_graph`) or must pass `edge_truth == exact` (`exact_effect_qualified_graph`). The route does possess the B grant in both arms, so the negative control isolates effect qualification rather than authorization. The qualified disjoint comparator retains its exact B edge.

`PASS_CONSTRUCTION`: 8/8 tests pass. The declared-only graph produces aggregate scores partial-overlap 9 versus disjoint-specialist 8. Enforcing the exact-effect edge gate on the same graph rejects `p_bc`→B (`partial`) and removes that apparent advantage: 8 versus 8. Both arms preserve all four offered task IDs, same fixed budget and total route capacity. An independently authored exhaustive assignment/replay implementation agrees on every per-scenario row. Four corruption mutations reject a false post-filter advantage, changing the disputed edge truth, and hiding or duplicating an offered denominator row.

This is an authored method-control construction result, not a formal container outcome, GUI effect observation, route qualification, or hypothesis pass. Formal candidate=0, independent auditor=0, retries=0. The pinned CPU image is cached, but the shared Docker daemon has other active work and the exclusive slot request on #5085 has no grant. The formal allocation remains frozen and unstarted.

## Earlier allocation-02 evidence

The v2 11/11 construction suite and its source hashes are preserved unchanged. Its unfiltered 9/8 versus filtered 8/8 values were observed only in an exploratory in-memory diagnostic after source review found the missing preregistered contrast; `effect_overlap_6278_portfolio_t0_v2/STOP.md` records that they are not formal evidence. Allocation 03 freezes the contrast and independent control implementation before any candidate/auditor container invocation.
