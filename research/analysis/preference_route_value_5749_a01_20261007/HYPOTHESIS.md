# Issue #5749 source-routing comparator — A01

## H / T / D / C / U

**H.** In a finite, authored choice model, a minimax-regret rule that prices clarification against its cost can distinguish low-consequence from high-consequence preference disagreement, while a source-only ACT/CLARIFY/VERIFY router treats both as the same user-goal uncertainty. It should avoid a costly question only when an explicitly authorized default has worst-case regret no greater than the frozen question cost; otherwise it must clarify or yield. Missing world facts should route to VERIFY before preference regret is scored. This tests a narrow #5749 decision boundary, not superiority of #5749 as a whole.

**T.** Nine frozen synthetic cases, each evaluated by (1) a source-uncertainty baseline and (2) a #5749-style minimax-regret rule. Candidate records contain finite supported preference rankings, admissible actions, optional explicitly authorized default, query/verification costs, and world-uncertainty status. The baseline is a deliberately simple deterministic abstraction: action disagreement routes to CLARIFY; otherwise unresolved relevant world state routes to VERIFY; otherwise propose the common admissible action or yield. It is informed by the ACT/CLARIFY/VERIFY decomposition in PROUR but is **not a reproduction of PROUR**, its learned policy, benchmarks, or reported metrics. The #5749 rule computes maximum regret over the supported rankings, clarifies only when that regret exceeds query cost and the answer is stipulated to resolve the ranking, otherwise proposes only an authorized default or yields. If no default exists, it compares query cost with the minimum worst-case regret over admissible actions but never proposes an action without authorization. Unknown preference sets yield. No models, users, GUI, network, or effects.

**D.** `PASS_METHOD_SCOPED` only if an independent auditor exactly reconstructs all 18 policy rows; the low- and high-regret pair has identical action-disagreement signals but falls on opposite sides of the fixed query-cost threshold; equality follows the preregistered no-query tie rule; world-only and mixed uncertainty route to VERIFY before regret scoring; absent preference evidence yields; low regret without an explicitly authorized default yields, while high regret without a default may clarify but may never propose an action; authority grants remain zero; and all six frozen corruptions are rejected. Any route, regret, authority, or completeness mismatch is FAIL; incomplete evidence is STOP/HOLD. No product or user outcome is inferred.

**C.** This operationalizes the #5749 worst-case-regret/query-cost idea against a toy source router. A different source-router threshold, a good authorized default, or more costly/less reliable questions can change the ranking. The comparator has no learned queries, probabilities, or calibrated interaction costs.

**U.** Utilities, query costs, and oracle answers are stipulated fixture values. The result does not validate the source router or PROUR, actual user preferences, answer reliability, GUI semantics, interruption burden, task effects, safety, or transfer. Preference evidence never grants execution authority; all outputs are proposals and `authority_granted` must remain false.

## Frozen parameters

- Policies: `source_router` and `regret_cost`.
- Allowed actions: A and B; any proposal remains subject to external authorization/admission.
- Clarification cost: case-specific; a successful answer is stipulated to identify the supported ranking exactly.
- Regret: `max_action utility - utility(proposed action)`, maximized over every supported ranking.
- Tie rule: if worst-case regret equals clarification cost, do not clarify; use only an explicitly authorized default, otherwise yield.
- Relevant unresolved world state is verified before preference regret is calculated.
- Allocation: `5749-ROUTE-REGRET-A01-20261007`; no retries or replacement allocation.

## Prior-art boundary

Li et al., [“Clarify the User or Verify the World? Uncertainty Routing for Proactive Agents”](https://arxiv.org/abs/2609.32255), motivates distinguishing user-goal disagreement from world-side uncertainty and routing among ACT/CLARIFY/VERIFY. This fixture's source router is only a fixed binary abstraction of that distinction; it is not the paper's learned PROUR policy or a reproduction of its benchmarks/results. The experimental question is the incremental finite behavior of #5749's consequence-regret/query-cost gate, not generic uncertainty routing novelty.
