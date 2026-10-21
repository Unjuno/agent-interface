# Issue #5749 action-only adaptation successor — A01

## H / T / D / C / U

**H.** Within an explicitly opted-in, reversible, context-bound assistance scope, a minimal action-only adapter can learn a repeated choice after two consecutive same-choice observations, reduce synthetic wrong suggestions relative to a fixed default and clarification-only policy burden relative to asking every turn, while one-off/conflicting actions, context changes, missing observations, or revoked consent never authorize durable adaptation or execution. This is the conditional successor described in Issue #5749, not permission to infer private utility from ordinary behavior.

**T.** Five frozen synthetic episodes with three deterministic policies (`static_default`, `clarify_each_turn`, `action_only_adaptive`), across 26 total turns per policy. The action-only state machine observes only explicitly marked user action events within the opted-in scope. It requires two consecutive matching observations; a conflicting observation suspends a learned choice and requires a fresh pair; an unconfirmed first observation pauses assistance for that turn; context or consent changes clear the learned/pending state before any proposal. No observed action or response is not evidence. Compare proposal matches to a separate fixture-only evaluator label, wrong proposals, yields, query count, and adaptation lag. All outputs are non-authoritative proposals; no model, user, GUI, network, or effect is involved.

**D.** `PASS_METHOD_SCOPED` iff an independent implementation exactly reconstructs all 78 policy-turn rows; stable repeated actions adapt after the second consecutive observation; a one-off/conflicting action never becomes learned state; changed feedback suspends the old learned choice before the next proposal; scope change and consent revocation clear state before output; missing observations do not train; clarification answers remain turn-scoped; and every row has `authority_granted=false`. The scripted stable-B episode must produce fewer wrong proposals than static default and fewer queries than clarify-each-turn. All seven frozen mutation controls must be rejected. Any mismatch is FAIL; missing evidence is STOP/HOLD. No human-benefit conclusion follows.

**C.** Static defaults can outperform adaptation when behavior is noisy or preference changes quickly. Clarifying each time may be appropriate when the consequences are high. Two matching observations are an arbitrary finite discriminator, not a selected or validated production threshold.

**U.** Episode actions and evaluator preferences are authored and may encode the answer; counterfactual user behavior is not modeled. This does not establish voluntary consent UX, stable preference, human correction burden, comprehension, privacy, task effects, reversibility, safety, or transfer. Explicit consent to this hypothetical adaptation is an input assumption; inferred preferences never grant execution authority.

## Frozen state-machine rules

1. The adapter is disabled unless the current turn carries explicit `consent=true` for the exact `scope_id`.
2. A scope change or `consent=false` clears both learned and pending choices before the current turn's proposal is produced.
3. With no learned choice, use only an explicit authorized default unless a first contrary action is pending; pending confirmation yields for that turn.
4. With a learned choice, propose it until a different action is observed; that observation immediately suspends the learned value and starts a pending value.
5. Two consecutive matching observed actions in the same opted-in scope establish only a scoped proposal preference. A missing action clears a pending (not a learned) value. Contradictory actions cannot accumulate across a gap.
6. Clarification-only asks each turn and uses only that turn's explicitly supplied answer; it stores nothing. Static-default never learns or asks.
7. No policy output performs an effect or grants authority.

Allocation: `5749-ACTION-ONLY-A01-20261007`. One formal candidate invocation and one independent audit; zero retries. Host/container runtime and exact source hashes are frozen separately in `FREEZE.json` before formal execution.
