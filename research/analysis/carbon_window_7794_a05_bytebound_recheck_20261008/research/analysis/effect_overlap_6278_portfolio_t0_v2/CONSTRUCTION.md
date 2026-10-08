# Construction history — allocation 02

Allocation `EFFECT-OVERLAP-6278-PORTFOLIO-T0-20261002-02` is distinct from the earlier boundary-only allocation in `effect_overlap_6278_t0_v1/`. Candidate=0, formal auditor=0 so far.

## Attempt 01 — comparator feasibility gate

`FAIL_CONSTRUCTION_COMPARATOR_INFEASIBLE`: the first authored library did not contain two equal-budget exact copies covering all three classes, and the universal route could not finish the four-task no-fault denominator by the common deadline. The test correctly refused to mark those comparator classes as losses. No formal invocation occurred. Before freeze, the library was corrected with two identical full-coverage route copies and a deadline-feasible universal fallback; all classes now pass the common nominal feasibility gate.

## Attempt 02 — current construction

`PASS_CONSTRUCTION`: 11/11 package tests pass. Candidate optimizer and independently authored exhaustive oracle agree on every portfolio score/winner, training/held-out assignment, control row and denominator. The tests include held-out leakage, fast versus late reconfiguration, short disturbance recovery, reallocation before deadline, authorization/unknown/partial-commit refusal, a universal-dominance no-advantage case, equal-budget/capacity bottleneck control, mandatory empty-input release, and seven raw-result mutation controls (denominator, unauthorized effect, committed replay, fabricated edge, aggregate, release time, winner). This is construction only; no formal run/result is claimed.

## Resource gate

The local Docker daemon is shared. The read-only inventory showed unrelated running containers `concentration-aware-ns:checker` and `unjuno-native-ci-6092`; Issue #5085 has concurrent resource-owner records. No existing container was inspected, stopped, signalled or modified. No exclusive CPU-container interval is currently recorded for this allocation. The candidate/auditor are deterministic standard-library Python; formal container execution remains at zero until a compatible isolated-container slot is explicitly awarded and rechecked. A host-only substitution will not be silently called the preregistered container run.
