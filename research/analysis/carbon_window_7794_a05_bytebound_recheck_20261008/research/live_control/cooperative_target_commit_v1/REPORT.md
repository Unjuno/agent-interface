# Cooperative target commit v1

Issue #401. Direct mechanism-class successor to the post-check selection race in #383.

## Result

`PASS_COOPERATIVE_TARGET_COMMIT_SCOPED`

The frozen 20-case matrix completed once with no formal reruns:

| arm | n | result |
|---|---:|---|
| generic stable A | 5 | 5/5 accepted; A +2, B 0 |
| generic observe A then switch B | 5 | 5/5 accepted; A 0, B +2 |
| cooperative observe A then switch B | 5 | 5/5 refused; A 0, B 0 |
| cooperative stable A | 5 | 5/5 accepted; A +2, B 0 |

The cooperative operation validates the expected target and performs the geometry mutation inside one serialized semantic critical section. No validation result is cached outside that section.

## Interpretation

This closes the deliberately injected check-to-effect race **inside this semantic fixture**: generic input acts on the current selection, whereas the cooperative operation refuses when the current target no longer equals the expected target.

The result supports the architectural distinction `observation != authority`: repeated visual checks only move the observation time, while a conditional effect-owner commit can bind validation to mutation when the effect owner exposes such a primitive.

## Limits

This is not an Inkscape API result. It does not show that ordinary Inkscape exposes a conditional target-validated effect operation. It is deterministic, in-process mechanism evidence only: no cross-process crash semantics, distributed transaction, authorization, performance, natural race frequency, or full GUI stack claim.

## Next question

Test the smallest real application boundary that can expose equivalent conditional semantics without modifying the target application: for example, whether an existing document/object API can identify the target and apply the mutation under one application-owned command/transaction. Do not add another screenshot polling rung.
