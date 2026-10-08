# Issue #5851 successor — intervention topology check

This successor tests a narrow issue in the original synthetic T0 protocol: the frozen candidate checks a +80 ms route-changing probe, then reports half-cost elasticities for each region without checking whether those actual half-cost interventions change route choice.

## H / T / D / C / U

**H.** For the original branch-change fixture, the declared half-cost model intervention changes the critical route; therefore reporting its endpoint delta as fixed-topology elasticity is invalid and should be classified `NONSTATIONARY_INTERVENTION`.

**T.** Reconstruct every endpoint-reaching path directly from the frozen original fixture. For each region, halve all member-node integer durations exactly as the original T0 specifies; compare the maximizing path set before and after. Separately reconstruct the declared +80 ms branch rule. Do not execute or alter the original candidate/auditor or their outputs.

**D.** PASS_COUNTEREXAMPLE if original candidate emits numeric half-cost model elasticity although the maximizing route differs (or tied path sets differ) under that intervention, and the independent enumerator reconstructs both path sets and costs. FAIL_NO_COUNTEREXAMPLE if it does not; HOLD_FIXTURE_ORACLE if endpoint/path interpretation is ambiguous.

**C.** A 3-node deterministic synthetic DAG with one alternate route outside the principal displayed edge list might still fully explain the declared route rule; the original case may have intentionally scoped its alternate endpoint outside the static graph. A fixed graph could be intended for half-cost elasticity even while only the separate +80 ms probe changes the actual route.

**U.** This only tests internal consistency of the frozen synthetic protocol. No real trace, GUI, GPU, task, safety, or performance claim. It does not prove a runtime bug.

Allocation: `CAUSAL-ELASTICITY-5851-BRANCH-INTERVENTION-20261001-01`
Base main: `b1f916e2c32a75069c68d570b27c390c25de3c91`
Original artifacts: `research/analysis/causal_critical_path_elasticity_5851_t0_v1/`
Candidate invocation: 1 independent JavaScript path enumerator; original candidate/auditor invocations: 0; GPU/container/model/GUI: 0.
