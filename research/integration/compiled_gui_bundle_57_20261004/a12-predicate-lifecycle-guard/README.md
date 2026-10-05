# A12 — planner predicate lifecycle guard

## Result

`PASS_SCHEMA_GUARD_CONSTRUCTION_SCOPED`. The frozen R02 schema accepts the exact archived provider contract even though `target_valid` appears in both action postconditions. The candidate v2 wrapper rejects that contract with a specific lifecycle error. Removing `target_valid` only from the two `expected_effect` lists yields a valid compiled graph; both action branches still require `target_valid=true`, and the submit postcondition still requires `exact_saved_title=true`. A negative control that removes `exact_saved_title` remains rejected by the baseline schema.

The candidate also records a prompt clause: `target_valid` is an observation-local target check, belongs in branch guards, and does not belong in post-action expected effects; fresh admission remains mandatory for every action. This is a candidate rule for this bounded planner vocabulary, not a general predicate type system or an updated formal runner.

## Reproduction and scope

`PLAN.md` was frozen before execution. The runner reads the SHA-pinned archived R02 task, baseline schema, prompt source, and compiled core; no model/provider, graph, GUI/input, network, container, or allocation is invoked. The audit independently verifies the source hashes, original-contract rejection, corrected graph guards/effects, and required-effect negative control. It uses explicit checks and produces identical results under normal Python and `python -O`. A tamper test that removes the preserved target guards is rejected in both modes.

- Raw SHA-256: `95ba3cb470ffe9166c0284a019afe3a967561eae24c539e1d5ffd27da4dc2f0c`
- Audit SHA-256: `66f60f7c20db8ce499165ffbd8b6bdcabe89cfce235f4f52f3f42f259b881812`
- Candidate SHA-256: `48549d1000a0a307436479fe64ae47fb0322d1e42f2a90a70e613691445526a7`

```sh
python3 run.py > RAW.json
python3 audit.py RAW.json > AUDIT.json
python3 -O audit.py RAW.json
```

## Limits

Only one retained contract was tested. No model call tested whether the prompt leads the model to produce the corrected contract; no task effect, transfer, authority/collateral behavior, end-to-end efficiency, or runtime adoption was measured. A11's counterfactual remains distinct from this schema test. R02's `9/12` graph result and REJECT disposition are unchanged. Any new live comparison needs a separately frozen allocation and independent review of the versioned prompt/schema pair.
