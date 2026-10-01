# #1462 retained model-branch cost identifiability v2

## Result

Decision: `PASS_RETAINED_MODEL_BRANCH_COST_NOT_IDENTIFIABLE_V2_SCOPED`.

This successor resolves the source-integrity failure mode of #1199 without modifying any v1 artifact. Four retained inputs were copied byte-for-byte from base main `c2826ec7cfb2aceaf55c9ef0e6fe1e9ed301692c`; Git blob readback matched all four before the only formal invocation.

Two independently structured analyzers agree:

- retained decisions: 24 (12 grouped + 12 ungrouped);
- grouped × ungrouped candidates: 144;
- exact same-image cross-arm pairs: 0;
- fully matched pre-branch pairs: 0;
- admissible different-branch matched pairs: 0;
- causal per-branch estimate emitted: no.

Analyzer A's gate failure counts over the 144 candidate pairs are: exact image 144, session state 144, cache counters 141, primary shape 130, effect memory 52, action state 0. Thus every candidate fails at least one required pre-model matchedness gate; image and session alone already exclude every pair.

The retained whole-run audit agrees with the normalized ledger. Grouped and ungrouped runs authored 4 and 6 contingencies respectively, but they are sequential divergent trajectories. Their token and model-wall differences are retained only as noncausal diagnostics. Dividing these differences by branch count would be invalid.

Provider-reported usage feasibility is independently present in both frozen probe documents. This shows the endpoint exists; it does not make the grouped/ungrouped arms matched.

## Controls

All four preregistered corruptions were rejected:

1. fake Analyzer-A admissible count → analyzer disagreement;
2. injected Analyzer-B pair → pair-set disagreement;
3. non-null causal cost → causal-laundering rejection;
4. one-byte ledger mutation → source/provenance HOLD.

## Scope

No new model call, provider call, GUI/X11 action or task input occurred. One formal container invocation; reruns/replacements/tuning 0.

The scientific conclusion is only that **existing retained evidence cannot identify marginal rich-model branch-authoring cost**. The next legitimate cost experiment is a fresh same-model/settings matched K1/K2 allocation with model-visible state, prompt/schema, cache/session provenance and non-branch output contract controlled. This v2 result must not be cited as a cost estimate.
