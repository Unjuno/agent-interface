# Additive correction to the frozen #1839 v1 result

This file corrects the interpretation of the historical v1 result without
editing any v1 source, freeze, result, or audit artifact.

## H / T / D / C / U

**H.** The v1 implementation rejects whitespace-only lineage identifiers and
requires a unique retained source-event reference for every accepted physical
edge and scorer event.

**T.** A read-only adversarial mutation changed `session_id`, `plan_id`,
`actuation_id`, `physical.owner_id`, and `task_effects[0].effect_id` to one
space each in a temporary copy of the frozen v1 raw result. The candidate and
oracle agreed on `PHYSICAL_ACTUATION_SCOPED` and `TASK_EFFECT_SCOPED`. The
unchanged raw-only auditor accepted the mutated result with zero errors and
returned `PASS_MAP01_TASK_EFFECT_CONTRACT_SCOPED`.

**D.** Overall interpretation: `HOLD_CONTRACT_GAP`. The mutation demonstrates
that v1's truthiness checks accept non-canonical whitespace identifiers, and
that its audit reconstruction does not require unique source-event IDs. The
v1 frozen artifacts remain byte-for-byte historical evidence; do not cite
their internal PASS string as satisfying the stricter successor contract.

**C.** Mutation result SHA-256:
`36d2d7a2daa6610a64555ad14436cc271ffaf82054e8caccc96afec9be0c839d`.
Original v1 raw result SHA-256:
`e26d8808d4238616f3868a48e628931a7c5e253dcc9664dfbfda6da77880be7e`.
Original v1 audit SHA-256:
`bd561cd6c0ae8837c41186fb97f423e57cb36d284cc1f252aa8c11ca2e3033c4`.

**U.** This was a synthetic post-freeze adversarial check, not a rerun of the
v1 allocation and not live evidence. It does not establish whether production
schemas can provide stable unique event IDs. Successor Issue #5126 owns that
question. No historical v1 bytes were changed.
