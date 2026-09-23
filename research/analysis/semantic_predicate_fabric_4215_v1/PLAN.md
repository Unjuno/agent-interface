# Semantic predicate fabric v1 — Issue #4215

Allocation: `semantic-predicate-fabric-4215-20260923-01`

## H
A single frozen local linear semantic backend can return a bounded batch of typed TRUE/FALSE/UNKNOWN predicates that drive a deterministic graph with final semantic correctness no worse than the same backend's direct disposition head, while preserving UNKNOWN and exposing reusable semantic facts to multiple graph nodes.

## T
Authority-neutral deterministic fixture in the provided Linux container, CPython standard library only. One frozen evidence representation; six predicates; one frozen linear backend family; 20 cases. Each semantic variable is represented by positive/negative evidence bits. The frozen score is `positive - negative`: +1=>TRUE, -1=>FALSE, 0=>UNKNOWN. An irrelevant toolbar feature has zero model weight. Compare one direct-disposition backend call versus one six-predicate backend call plus deterministic graph per case. Cases include same state/different intent, single predicate branch flips, irrelevant-only changes, missing evidence, conflicting evidence, out-of-envelope and mixed priority controls.

## D
`PASS_SEMANTIC_PREDICATE_FABRIC_SCOPED` only if all 20 cases/120 predicate labels execute once; predicate accuracy=1.0; UNKNOWN precision=recall=1.0; joint all-predicate correctness=1.0; graph disposition accuracy=1.0 and is not worse than direct action accuracy; direct action accuracy=1.0; UNKNOWN is never executable TRUE/FALSE; semantic errors masked/amplified=0; one backend call per case per arm; at least one predicate is consumed by multiple graph nodes without another backend call and reuse reads>0; authority_granted=false everywhere; independent raw audit errors=[]; >=10 coherent evidence mutations reject; formal1/reruns0/replacements0/exclusions0/tuning0. Predicate error => FAIL_PREDICATE_FIDELITY; UNKNOWN collapse => FAIL_UNKNOWN_COLLAPSE; graph worse than direct => FAIL_GRAPH_AMPLIFICATION; zero compositional reuse => HOLD_DIRECT_ACTION_SIMPLER; provenance/source/integrity ambiguity => STOP/HOLD.

## C
The frozen linear backend is an authored single candidate, not Laya/Kev and not a claim of learned semantic quality. The oracle is synthetic and independent of candidate output. The graph may encode the same semantics as the direct head; this rung tests the representation boundary and structural fact reuse, not model-selection superiority.

## U
No GUI/task input, provider/model service, natural semantic error distribution, model-token saving, live planner benefit, authority, production runtime, or cross-domain generality claim. Timings are descriptive only.
