# Versioned predicate specialist switch — #4284 formal result

Allocation: `versioned-predicate-specialist-switch-4284-20260923-01`  
Disposition: **PASS_VERSIONED_PREDICATE_SPECIALIST_SWITCH_SCOPED**

## Result

One prospectively hash-frozen authority-neutral formal invocation completed 60/60 cases (10 lifecycle schedules × 3 policies × 2 repetitions), 462 lifecycle rows, with reruns/replacements/tuning 0/0/0.

The candidate `SHADOW_VALIDATED_VERSIONED_SWITCH`:

- never activated in PREPROMOTION_MATCH;
- activated only after the frozen four consecutive same-identity zero-disagreement shadow rows;
- preserved independent predicate and guarded-graph semantics on every candidate row;
- preserved required UNKNOWN without executable collapse;
- fell back to GENERAL for a novel target encoding;
- invalidated the old activation before specialist use on support-version, producer-generation, and stale-activation-receipt schedules;
- refused activation of the directed regression specialist;
- recovered with a separately shadow-validated v2 under a distinct activation identity;
- retained `authority=false` on every row and activation receipt.

In STABLE_ACTIVE, candidate GENERAL-backend call ratio was 4/16 = 0.25 in both repetitions versus ALWAYS_GENERAL, below the frozen <=0.30 gate.

The diagnostic `UNGUARDED_SPECIALIST_SWITCH` is retained as an intentionally unsafe comparator and is not promoted.

## Evidence

- formal cases: 60/60
- lifecycle rows: 462
- formal invocation/rerun/replacement/tuning: 1/0/0/0
- raw-only audit: errors=[] / PASS
- corruption controls: 13/13 rejected
- RAW SHA-256: `711f67b0e615ec6b4fc58dddedd490724369b6476ff6036f52e34536e72114e9`
- RESULT SHA-256: `3ad05fcab33a8427892cd441d74d318dda85bbe8c2627596a2579ba8627d6d64`
- AUDIT SHA-256: `ff8cfd76805baa9356bce536eb621c968221aa5a1a8cfcadeb203d4dc8a285ff`
- CONTROLS SHA-256: `244e107badae96f0b1749be9979a9858ec60abfab1541149d7fd215321805b2f`
- lossless evidence/source archive XZ SHA-256: `a35457c72f7dffed7351e2f6b9590744e3ab323418a462f413d7ea4f85a6711d`

The preformal publication formatting mistake for construction controls was detected and corrected before formal invocation; the exact frozen blob then matched local bytes. Scientific source SHA-256 values remained unchanged through formal execution.

## Interpretation

This finite deterministic fixture supports a narrow lifecycle contract: a versioned semantic-predicate specialist can reduce general-backend calls on stable in-envelope rows while failing closed on novelty, identity invalidation, stale activation, and directed regression, without changing graph semantics or execution authority.

It does not establish that automatic specialist lifecycle management is worthwhile in production. The parent specialist is a four-entry lookup derived from an authored linear predicate; regenerating or directly coding the rule may be simpler than maintaining the activation machinery.

## Scope / limits

No OS input, live model/provider, natural drift distribution, task effect, token saving, cross-application/cross-platform validation, automatic model deployment, or product/runtime promotion. `authority=false` throughout. A PASS here is a semantic-provider lifecycle result only.
