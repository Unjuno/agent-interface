# Token-qualified owner-release reconciliation

This callable composes the retained error-field-aware owner-release audit with the separate token ownership precheck. Missing, shared, malformed or otherwise ambiguous admission tokens yield `HOLD_AMBIGUOUS_TOKEN` before owner rows can be attributed. When the precheck is ready, the retained auditor evaluates explicit transitions and terminal owner cleanup, including its error-field checks. The output is scoped; `formal_pass` remains false.

This is not a complete operation-identity audit: the retained owner reconciliation matches by token and key count, not by admission step; terminal cleanup attempts lack independently verified per-admission identity. The precheck considers all admissions and can conservatively hold when unrelated admissions exist. Neither a scoped PASS nor HOLD establishes physical release, task effect, provenance or MAP01 completion. Historical raw and results were not inspected or modified.

Synthetic tests cover cross-cancellation token reuse, missing cleanup error fields and the existing unique-token terminal cleanup fixture. No GUI, input, game or model is used.
