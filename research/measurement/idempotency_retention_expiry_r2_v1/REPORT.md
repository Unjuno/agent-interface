# #24 idempotency retention expiry R2

Decision: **PASS_EXPLICIT_EXPIRY_UNCERTAINTY_SCOPED**

## Question
R1 showed that an authoritative status query should precede replay after a missing ordinary receipt. R2 asks what happens when that detailed status record is subject to bounded retention.

The one changed factor is expiry disposition:
- `DROP_TO_NOT_FOUND`: an expired known operation becomes ordinary `NOT_FOUND`, which R1 treats as retry-eligible.
- `EXPLICIT_EXPIRED_UNKNOWN`: a known identity that reached input becomes `EXPIRED_UNKNOWN`; it grants no authority and is not replay-eligible. Failed-before-input history may age to `NOT_FOUND`.

Detailed status is valid iff query age is `<1000 ms`; `>=1000 ms` is expired.

## Formal result
Frozen seed `240220260918002`; one invocation; 160,000 traces / 320,000 paired rows; reruns/replacements/tuning 0.

- candidate duplicate non-idempotent effects: **0**
- DROP_TO_NOT_FOUND comparator duplicate effects: **50,071**
- candidate/oracle mismatch: **0**
- candidate unsafe replays after expired may-have-effect history: **0**
- retry eligibility preserved for expired FAILED_BEFORE_INPUT + truly never-seen: **40,000/40,000**
- altered-parameter/cross-session new effects: **0**
- authority promotions: **0**
- false COMPLETED claims: **0**
- outcome digest: `c0fb3ed264cdc2d689c4d8da2d891668172ef3d88b8386dfe6135eb80d2fe5c0`

The comparator duplicates comprise all 20,000 completed-at-expiry, all 20,000 completed-after-expiry, and 10,071 hidden-effect-positive EFFECT_UNKNOWN traces. The candidate never reads hidden effect truth; after detail expiry it retains only typed uncertainty.

Independent audit regenerates the full corpus and passes. Four copied-result corruptions are rejected.

## Interpretation
Bounded storage expiry must not silently convert a known may-have-effect identity into ordinary never-seen `NOT_FOUND` when `NOT_FOUND` is replay-eligible. A minimal expired/unknown marker is sufficient in this synthetic contract to preserve uncertainty without keeping the complete historical status forever.

This is a semantic requirement, not a production storage design. A system may use content-bound durable outcomes, effect revalidation, a secondary tombstone window, or conservatively non-retryable operation classes instead of this exact representation.

## Limits
Standard-library state machine only. No disk durability, power-loss, GUI effect observation, cross-process persistence, planner-boundary reduction, tokens, latency or memory-cost optimization is established. The ultimate expiry of the tombstone/identity marker is not solved by this rung.
