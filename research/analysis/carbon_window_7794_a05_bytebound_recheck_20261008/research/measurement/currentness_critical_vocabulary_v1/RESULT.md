# Currentness critical vocabulary adequacy v1 — retained first outcome

Decision: **`PASS_CURRENTNESS_VOCABULARY_GAP_SCOPED`**.

The five frozen source-derived `observable_signal_guard_v2` required cases (`HARD_INVALIDATED/below_hard_minimum` plus four representative `UNKNOWN` reasons) have **zero admissible mappings** into the six existing #1021 critical kinds under the predeclared entailment predicates.

Positive/negative controls discriminate correctly:
- verified focus release -> `FOCUS_CHANGED`;
- verified expiry release -> `LEASE_EXPIRED`;
- owner failure -> `SAFETY_VIOLATION`;
- viewport-only visible change -> no `EFFECT_VERIFIED` mapping.

The retained gap is semantic, not queue-mechanical. `HARD_INVALIDATED/UNKNOWN` establish currentness/evidence invalidation and a need for a new decision, but do not by themselves establish prior authority revocation, action rejection, focus change, lease expiry, safety violation, or verified semantic effect. Mapping them to one of those kinds would add an unsupported assertion.

Formal invocation: 1; reruns: 0. Independent audit PASS with errors `[]`; corruption controls reject 5/5. Model/provider/GUI/task-input/authority actions: 0.

Scope: source-level vocabulary adequacy only. This does not add a new kind or prove a production ABI. The next bounded rung is to add one explicit critical `CURRENTNESS_INVALIDATED`-style kind and verify #1021 reducer semantics remain unchanged except accepting/preserving that new critical role before integrating the guard adapter.
