# Frozen T0 preregistration — Issue #6351

- Issue: https://github.com/Unjuno/agent-interface/issues/6351
- Source `main`: `645bc89c71f28a88d8ff37f995d56057cb4cf734`.
- Allocation: one deterministic CPU-only synthetic allocation; no model, GUI, user data, participants, or runtime changes.
- H — On identical source evidence, a flattened summary can induce at least one unsupported/contradictory conclusion among planner, verifier, and effect/obligation owner, while machine-role projections preserve invariants. Null: directly queried typed receipts already preserve all distinctions at equal or lower cost.
- T — Freeze eight non-handoff event histories spanning dispatch-only, released/no-effect, verified effect, wrong-target effect, delayed effect, incomplete child obligation, explicit UNKNOWN, and contradictory receipts. For each compare flattened, direct typed-receipt queries, and role projections over the same immutable core. Independently score claims against a separately specified truth table, contradictions, unsupported inferences, omitted obligations, false completion, and reconstruction field lookups. Apply four corruption controls (epoch swap, drop child obligation, relabel acceptance as effect, and collapse CONFLICT to PASS).
- D — `METHOD_PASS_SCOPED` only if all direct-query and projection claims agree with the oracle, all planted corruptions are detected, and projections reduce reconstruction lookups versus direct typed queries without losing an invariant. `CONSOLIDATE_NO_INCREMENTAL_VALUE` if direct typed queries preserve every hard distinction and projections add no correctness gain (regardless of lookup count). `FAIL_METHOD` if a projection makes an unsupported claim, hides an obligation, equates dispatch with effect, or normalizes conflict. `HOLD` for any ambiguous oracle or audit mismatch.
- C — Existing typed receipts plus direct queries may be sufficient; apparent drift may be caused by stale/missing events rather than presentation.
- U — Eight deterministic synthetic histories test method mechanics only. Agreement does not prove external effect, truth of the shared core, model behavior, human reliance, production schema suitability, or broad semantic interoperability.
- Candidate and independent auditor: one invocation each after freeze; no retries. Any failure is retained as-is.

No results were generated when this preregistration was frozen.
