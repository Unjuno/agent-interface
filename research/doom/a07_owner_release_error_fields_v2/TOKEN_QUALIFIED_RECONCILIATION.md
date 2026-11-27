# Token-qualified owner-release reconciliation

This callable composes the retained error-field-aware owner-release audit with the separate token ownership precheck. Missing, shared, malformed or otherwise ambiguous admission tokens yield `HOLD_AMBIGUOUS_TOKEN` before owner rows can be attributed. When the precheck is ready, the retained auditor evaluates explicit transitions and terminal owner cleanup, including its error-field checks. The output is scoped; `formal_pass` remains false.

This is not a complete operation-identity audit: the retained owner reconciliation matches by token and key count, not by admission step; terminal cleanup attempts lack independently verified per-admission identity. The precheck considers all admissions and can conservatively hold when unrelated admissions exist. Neither a scoped PASS nor HOLD establishes physical release, task effect, provenance or MAP01 completion. Historical raw and results were not inspected or modified.

Synthetic tests cover cross-cancellation token reuse, missing cleanup error fields and the existing unique-token terminal cleanup fixture. No GUI, input, game or model is used.

The current input-owner v12 emits `intent_token` on the owner-release receipt. For a cancellation with admissions, the qualified callable requires exactly one owner-release receipt whose token matches the admissions; a missing or different token yields `HOLD_OWNER_RELEASE_IDENTITY`. Historical source/schema compatibility is unverified, so missing legacy fields are treated as insufficient evidence, not as an observed unsafe release.

For cancellations with admissions, each integer `admitted_ns` must be strictly earlier than the integer `requested_ns`; missing, malformed, equal or later times produce `HOLD_ADMISSION_ORDER`. This compares recorded numbers only: a shared monotonic clock and truthful provenance require separate evidence. No-input cancellations do not need an admission-time comparison. Historical A07 raw was not examined.
