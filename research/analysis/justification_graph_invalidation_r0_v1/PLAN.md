# #1816 Exact invalidation semantics for justification graphs

TASK: `JUSTIFICATION-GRAPH-INVALIDATION-ANALYTIC-R0-20260919-001`

Parent #1659. This rung isolates monotone truth-maintenance semantics before choosing a persistent graph implementation.

## H
Each derived claim owns a finite OR-of-AND family of justifications. A claim is valid iff at least one justification has all supports valid. In an acyclic complete declared support graph, retracting base evidence has a unique correct derived state: evaluate claims in topological order, equivalently iterate invalidation to the least fixed point.

Naively invalidating every descendant is strictly over-invalidating when an unaffected alternative justification remains satisfied. Omitting a true causal support can instead false-retain a claim.

## T
Frozen finite family:
- roots E0,E1,E2 and claims C0,C1,C2;
- each claim's candidate justification is any singleton or pair of earlier nodes;
- each claim's justification family contains one or two distinct candidate justifications;
- family counts 21,55,120 -> 138,600 acyclic structures;
- each structure: 8 source-root valuations x 7 nonempty root-retraction masks = 56 conditions;
- total 7,761,600 conditions.

For each structure, precompute all eight topological root-state outcomes, compare them against a separate iterative fixed-point evaluator, then inspect all 56 source/retraction conditions for dependency-closure preservation and a naive descendant-invalidation baseline. Retain a hidden-edge false-retain discriminator. Independent auditor recomputes the structure/root-state equivalence from constants.

## D
PASS iff structure count138,600, condition count7,761,600, topo/fixed-point mismatch0, unsupported derived-state errors0, changes outside retracted dependency closure0, at least one naive over-invalidation witness, hidden-edge false-retain witness, corruption controls pass, independent audit PASS, and formal1/reruns0/replacements0/tuning0.

## C
Cycles, negative/default reasoning, probabilistic support, priorities, temporal expiry and incomplete declarations are outside this positive acyclic model.

## U / stop
Semantic theorem only. No runtime structure, performance, persistence, model, GUI or product claim. Stop after first deterministic formal result and independent audit.
