# A02 plan — authorized source-bound conditional deferral

Issue #6422 comment 5944099107 refined T0: only a condition stated by an authorized required principal, and independently verified against the named condition, can make a fresh approval request eligible. It never grants effect authority. The earlier A01 output is retained unchanged and is treated as partial evidence.

## Question and hypothesis

Does adding a fail-closed principal-membership check to A01's conditional-deferral eligibility rule reject valid-looking deferrals from non-required, unmapped, or absent principals, while preserving a fresh request after an authorized source-stated condition is independently verified?

## Frozen finite design

Eight authored no-effect cases: authorized valid deferral; non-required observer with an otherwise valid receipt; unmapped principal with valid receipt; missing authority mapping; wrong predicate; agent-asserted receipt; wrong evidence kind; and condition not stated by the source. Compare the A01 behavior with the guarded rule. The guarded rule asks for a fresh decision only for the first case. All other cases HOLD. Every output has `effect_authorized=false`.

The positive case requires exact predicate and evidence-kind match, a source-stated condition, an independent receipt checker, a valid receipt, and a principal present in the frozen required-principal set. Missing or malformed authority is HOLD.

## Decision and limits

`PASS_METHOD_SCOPED` requires exact eight-row reconstruction, A01 baseline showing the targeted unauthorized eligibility, guarded unauthorized eligibility zero, zero effect authorization, and rejection of all five raw corruption controls. This only tests finite authored policy mechanics. It does not establish a runtime contract, model behavior, user pressure, human benefit, or actual effect prevention. It is not completion of all #6422 T0 requirements (including interruption-budget behavior).

## Execution boundary

Frozen against repository main `eacb1346866f660d9d34eb36cd9691fd8184e5ff`; issue refinement comment `5944099107`; branch `research/denial-aware-deferral-authority-6422-a02-20261002`. Windows host CPU / CPython 3.11.9 only. No model, person, GUI, WSLc, Docker, GPU, CUDA, network-dependent experiment, or effect.

