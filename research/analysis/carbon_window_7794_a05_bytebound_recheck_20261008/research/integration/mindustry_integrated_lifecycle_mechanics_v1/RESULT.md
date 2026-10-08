# Mindustry integrated persistent lifecycle mechanics v1 — retained first outcome

Task: `MINDUSTRY-INTEGRATED-LIFECYCLE-MECHANICS-20260917-001`  
Issue: #851  
Publication base: `488ecc39b6ede63d6f357ee52ed96be3df58552f`

Disposition: **`PASS_MINDUSTRY_PERSISTENT_LIFECYCLE_MECHANICS_SCOPED`**.

The source-first frozen container formal runner was invoked exactly once; formal reruns were zero. The independent auditor passed every transition/effect invariant. Four structured result-corruption controls were all rejected. No provider/model call, GUI, Mindustry process, X11 input, network task action, or user-data action occurred.

## Frozen valid lifecycle

| phase | result | logical generation charge |
| --- | --- | ---: |
| cold | `INSTALLED` P1/W1/M1 | 1 |
| reuse_A1 | `EFFECT_VERIFIED` | 0 |
| reuse_A2 | `EFFECT_VERIFIED` | 0 |
| invalidate_B | `STALE_WORLD_BINDING`, zero effect | 0 |
| repair_B | `REPAIR_PROMOTED`, W1→W2 only | 1 |
| reuse_B1 | `EFFECT_VERIFIED` | 0 |
| reuse_B2 | `EFFECT_VERIFIED` | 0 |

The four accepted task effects are unique/exact-once. The valid trace ends with no owned resources. Palette generation remains P1 and method remains M1/version1 across the world-only invalidation and repair.

`logical_generation_charge` is a fixture accounting field used to verify the #57 lifecycle shape. It is **not provider usage** and no real model was called.

## Negative controls

- old W1 replay after W2 promotion -> `STALE_WORLD_GENERATION`, zero effect;
- repair without fresh current evidence -> `REPAIR_REFUSED`, no version mutation;
- repair attempting palette/method mutation -> `OVERBROAD_REPAIR_REJECTED`;
- duplicate task replay -> `IDEMPOTENT_REPLAY`, no second effect;
- missing binding evidence -> `NO_TARGET_AUTHORITY`, zero effect.

Corruption controls separately mutate the retained result to create a stale-authority escape, palette mutation, extra reuse generation and duplicate second effect. The independent auditor rejects all four.

## Interpretation

This closes only the **deterministic composition skeleton** behind #846 cells 9/11/12: model-free reuse can be represented with zero new logical generation, a world dependency change can invalidate only the world binding, selective repair can preserve unrelated palette/method identities, and reuse can resume after repair.

It does **not** retroactively mark #846 cells 9/11/12 as live Mindustry passes. Real image/binding quality, OS-input behavior, independent engine effects under this composed path, provider token/latency savings, and the matched plain/current-optimized/persistent three-arm economics remain unmeasured. #57 cell 13 therefore remains open.

## Integrity

- formal invocation: 1; reruns: 0; provider calls: 0;
- source-first freeze commit: `649f22ada37405d0a77c67e2050a82abc0e0889f`;
- RESULT SHA-256: `b6edbfcc4f72541caffc6bb99091efbb944800a5ef56d89d47350c8ef18113e8`;
- AUDIT SHA-256: `330043e15fbe7ae491c492484479beeee5a8b2f63f8188c702b450f6b4b7e368`;
- CORRUPTION SHA-256: `5d1a576867c605c5acae8c813846161af7d75092decd5f261598bffe93b00b87`.

Next work must be a separately coordinated real Mindustry transfer or the final matched three-arm allocation; do not infer live readiness from this state-machine PASS alone.
