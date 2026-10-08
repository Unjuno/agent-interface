# Frozen corrective successor allocation A02 — Issue #6351

- Parent: `../cross_role_meaning_drift_6351_t0_v1/`; A01's exact outputs are preserved under `invalidated-a01/` and are invalid for inference because its auditor hard-coded corruption detections and lookup counts.
- Issue: https://github.com/Unjuno/agent-interface/issues/6351
- Source `main`: `645bc89c71f28a88d8ff37f995d56057cb4cf734` (source-bound synthetic method test; no runtime behavior).
- One deterministic CPU-only OrbStack allocation; no model, GUI, user data, participants, or runtime changes.
- H — With identical immutable evidence, an untyped flattened summary can make at least one of planner, verifier, and effect/obligation owner infer a false completion or lose a hard distinction. Direct role-specific typed-receipt queries and invariant-core role projections should preserve all distinctions. Null/Issue-mandated consolidation: direct typed queries already suffice, so projections add no correctness value.
- T — Eight non-handoff event histories: dispatch-only; released/no-effect; verified effect; wrong-target effect; delayed effect; verified effect with unresolved child; explicit UNKNOWN; contradictory receipts. Compare flattened summary, direct typed queries and role projections against a separately frozen oracle. A separate mutation suite physically mutates raw objects for epoch mismatch, dropped child, ACCEPTED relabelled as effect, and CONFLICT relabelled PASS. Each mutation must be rejected by the same independent invariants; no counters may be hard-coded.
- D — `CONSOLIDATE_NO_INCREMENTAL_VALUE` if typed baseline and projections both pass all row invariants and all mutations are rejected; `METHOD_PASS_SCOPED` only if projections preserve all invariants and typed baseline demonstrably fails one under identical evidence; `FAIL_METHOD` if a projection loses an invariant; `HOLD` on any oracle/auditor inconsistency.
- C — Existing typed receipts may already answer all bounded role questions; flattening is an intentionally lossy negative control, not a proposed production baseline.
- U — Finite synthetic semantics only; cannot prove real event provenance, true effects, model or human interpretation, runtime suitability, or broad interoperability.
- Candidate once and independent raw-only auditor once; no retries.

The frozen dataset and source hashes are retained in `FREEZE.sha256` before execution.
