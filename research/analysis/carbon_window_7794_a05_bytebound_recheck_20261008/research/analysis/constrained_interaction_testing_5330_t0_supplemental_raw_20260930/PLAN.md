# Issue #5330 T0 constrained interaction-testing experiment

## H — scoped hypothesis
For the declared ten-binary-factor synthetic workflow, a constrained pairwise/three-way design plus deterministic strength escalation detects more registered cross-factor hazards than one-factor-at-a-time at measurable run cost, while unconstrained random sampling may spend runs on dependency-invalid assignments. This tests design mechanics only; the injected hazard oracle is fixture truth.

## T — frozen finite matrix
- Enumerate all 1,024 assignments over freshness, lease, handoff delivery, owner state, capability enforcement, protocol order, backend delay, retry, concurrent actor, and evidence summary.
- Constraints: lost handoff requires active owner; duplicate retry requires delayed backend or lost handoff.
- Registered hazards: stale+expired lease; lost handoff+active owner+concurrent actor; capability bypass+reordered protocol; expired lease+delayed backend+duplicate retry; stale+compressed evidence+capability bypass.
- Compare one-factor-at-a-time, deterministic constrained pairwise, deterministic constrained three-way, fixed-seed unconstrained random chaos with budget equal to the three-way array, and one-/two-/three-way strength escalation with black-box binary hazard classification and deletion-minimization probes.
- Check three declared metamorphic relations over the first 12 pairwise rows: opaque task-ID rename, evidence-order reversal, and irrelevant metadata addition.

## D — frozen gates
PASS_T0_SYNTHETIC_DESIGN iff the constrained arrays cover every feasible interaction pattern at their declared strength; every row and hazard outcome agrees with a separately coded raw-only oracle; all metamorphic cases preserve classification; every modeled hazard stops before effects; constrained designs contain no invalid assignments; corruption controls reject altered decisions, missing rows, invalid-row admission, and a nonzero simulated effect.
FAIL_DESIGN_ORACLE on any mismatch. STOP_INTEGRITY on source/result hash or audit integrity mismatch. Report random invalid cases and all limits; they are observations, not automatic scientific failures.

## C — controls
Only the declared publication policy/design changes. All methods use the exact same finite configuration space, constraints, fault predicates, classifier and zero-effect simulator. Chaos uses fixed xorshift seed 0x5330, without replacement. No task IDs, timestamps or metadata influence classification except in explicit metamorphic probes. No live agents, GUI, inputs, containers, model calls, GPU/CUDA, or external effects. A host-isolated in-memory finite model is used because the available C: volume is critically low and no shared container lease is assigned.

## U — limits
Synthetic deterministic fault rules are author-defined and not empirical frequencies. Ten binary factors, two explicit constraints, five predeclared faults and one deterministic tie-breaker do not establish coverage of actual runtime failures, a general locating array, safe chaos engineering, issue prevalence, production safety, or benefit. Adaptive escalation is only a finite T0 implementation; no live recovery/authority handoff is tested.
