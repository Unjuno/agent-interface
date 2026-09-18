# Effect-pending planner overlap analytical R0

Issue #1616.

## Claim
A verified token-bound empty physical release may make planner reasoning resumable while TASK_EFFECT remains pending, provided the client state never grants new input authority and treats effect/timeout/terminal as orthogonal typed evidence.

## Assumptions
- One action is already accepted with fixed action_id=A and intent_token=T.
- Event delivery is a total order for this analytical model.
- RELEASE_OK represents verified owner release with empty keys/buttons and matching token.
- EFFECT_OK represents a current, matching, unique TASK_EFFECT receipt with input_authority=false and semantic_authority=false.
- TIMEOUT is the unique bounded unresolved-effect outcome.
- TERMINAL_OK is a matching terminal only; it does not imply task effect.
- Stream loss, clocks, concurrent socket delivery, and backend reordering are outside this R0 model.

## H/T/D/C/U
H: release-resume and effect-pending compose without authority escalation.
T: exhaustive candidate-vs-independent-history-oracle comparison for every trace length 0..5 over 8 event symbols, plus corruption controls.
D: PASS iff all traces agree, invariants have zero violation, and five corruption controls reject. Any mismatch/coercion => FAIL.
C: omitted runtime loss/reordering/timing could invalidate live transfer without invalidating this scoped semantic result.
U: finite contract model only; no live benefit, latency, GUI, or production claim.
