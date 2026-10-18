# A11 — transient target predicate in post-action effects

## Result

`PASS_SCOPED_CONTRACT_COUNTERFACTUAL`. The retained R02 block-2 C/task-1 trace contains three relevant observations: the target check and field entry are valid at sequences 13 and 20; after Submit, sequence 25 records `exact_saved_title=true` and `target_valid=false`. The archived provider contract included `target_valid=true` in `save_value.expected_effect`, so the pinned core correctly returned `SAFE_YIELD/effect_failed` after two completed actions. The independent R02 scorer credited task-1 as exact (`exact_counts.task-1 = 1`); the arm still failed overall because task-4 was missing.

I replayed those three retained predicate states through the exact archived core with mock observe/admit/execute/effect callbacks. The only positive-case contract edit removed the transient target check from `save_value.expected_effect`; it remained in the pre-action branch and ordinary per-action admission. With that single change, the graph completed. Two controls changed only the final saved-title predicate: `false` yielded `effect_failed`, and `unknown` yielded `effect_unavailable`. No success verifier ran for either negative control.

This supports a narrow ABI interpretation: target validity is a fresh pre-dispatch guard, while `expected_effect` contains post-action facts. The frozen planner schema currently accepts `target_valid` as an action effect and does not encode that distinction, which leaves the model contract ambiguous. A versioned prompt/schema constraint is a plausible next repair to evaluate; this counterfactual alone does not establish general semantics or fix the contract generator.

## Provenance and verification

`PLAN.md` was fixed before the valid run. `run.py` verifies the archived task/core/schema/compiler SHA-256 values and reconstructs only the recorded sequences 13/20/25. `audit.py` independently reopens the retained task, checks its predicate sequence, verifies the four outcomes and action/effect-verifier traces, and uses explicit checks. Normal and `python -O` audit outputs match. A tampered record that reports success with a false saved-title predicate is rejected in both modes.

- Raw SHA-256: `e5b7c8ac9a0113cd2d763851612b60b57277826a50bf8bbc6f64a8b13fccd700`
- Audit SHA-256: `716e0db07f7a74e7c23ede5dad93b50d610362aa4d372200d6d7657ac36b673e`
- Runner SHA-256: `f11e7baf71034a05ccf181db737b7123918eb92716b80c6bac5f355941b30bf7`
- Auditor SHA-256: `c7c292aa3355ae06c0436a4cf7e13aa474abc66fc6e0e6e018a4e2b5df505edc`

Reproduce with:

```sh
python3 run.py > RAW.json
python3 audit.py RAW.json > AUDIT.json
python3 -O audit.py RAW.json
```

The first runner invocation stopped before producing a raw because the scratch import path omitted the archived schema directory. That harness-only error was corrected before the valid run; the scientific decision rule and frozen input were unchanged.

## Limits

All actions and effect-verifier responses here are test doubles; no app state was changed or rescored. The runner consumes retained observation predicates rather than pixels and does not call the model. It does not qualify the observer, prove the R02 task's physical effect, change the historical R02 disposition, show efficiency, establish transfer, or authorize another formal allocation. The R02 arm remains 9/12 graph successes and rejected on its full gates; other arm/task results remain unchanged.
