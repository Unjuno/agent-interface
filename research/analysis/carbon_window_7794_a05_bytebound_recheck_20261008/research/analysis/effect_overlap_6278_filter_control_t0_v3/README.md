# Issue #6278 — same-graph qualification filter control

## H / T / D / C / U

**H:** A partial-overlap portfolio can show an apparent reallocation advantage when a route's advertised class is treated as qualified; if the only path for a needed class has partial rather than exact effect truth, enforcing the exact-effect edge gate removes that apparent advantage against an otherwise equal disjoint comparator.

**T:** Use one frozen synthetic task mix, route graph, budget, capacity, and three dependency scenarios. Score the declared-graph view and then the *same graph* after applying exact-effect edge qualification. Both arms use the same exhaustive assignment objective and deadline/capacity scheduler; a separately implemented exhaustive auditor reconstructs all rows. Authority remains unchanged and the disputed route already has the corresponding grant, isolating effect truth. Training/fault set: no fault, left-dependency loss, right-dependency loss. This is a narrow negative control, not a new route-portfolio benchmark.

**D:** `PASS_FILTER_CONTROL_SCOPED` only if the exact same partial-overlap graph strictly exceeds the disjoint comparator before edge qualification, the two are tied after the partial edge is rejected, all offered rows/cost/capacity/deadline data reconcile, and independent exhaustive replay agrees. `FAIL_CONTROL` if the gain persists after filtering, if declared and qualified arms differ in anything besides effect-edge eligibility, or if the independent audit differs. No H_PASS or empirical agent-interface claim is available.

**C:** This is a hand-authored graph and scenario table; one small equal-budget instance cannot establish prevalence. The pre-filter arm deliberately represents declared labels only and is not an eligible execution policy.

**U:** No GUI, route qualification, natural fault distribution, readiness decay, application effect, product reliability, or live fallback is measured. The unfiltered arm is a diagnostic counterfactual, never authority to execute.

## Lineage

Allocation 03 follows allocation 02's pre-candidate `STOP_PRE_CANDIDATE_MISSING_FILTERED_GRAPH_NEGATIVE_CONTROL`. Allocation 02's frozen files and STOP remain immutable. This successor freezes only the omitted same-graph edge-qualification discriminator and reuses no formal output or claim from its predecessor.
