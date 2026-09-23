# #1564 observation gating tiny-change aHash stress — retained formal result

Task: `OBSERVATION-GATING-TINY-CHANGE-AHASH-STRESS-20260918-001`

Decision: **`PASS_TINY_CHANGE_STRESS_REJECT_GLOBAL_AHASH_SCOPED`**.

## Question

The existing O1 observation gate suppresses only byte-exact unchanged frames and retained zero false suppressions. The project roadmap explicitly requires adversarial stress before any approximate/perceptual gate can be trusted with small semantically important GUI changes.

This rung isolates one common global 64-bit average-hash style gate. It does not modify or reinterpret O1/O2.

The synthetic frame is an exact 64x64 grayscale state represented by 64 uniform 8x8 blocks plus sparse pixel overrides. aHash compares each block mean to the global mean. Tiny families are declared MUST_FORWARD by the frozen corpus contract.

Two policies are compared:

- `GLOBAL_AHASH_ONLY`: suppress when the 64-bit hashes are equal.
- `AHASH_PLUS_EXACT_FALLBACK`: unequal hash forwards immediately; equal hash performs exact representation comparison and suppresses only exact equality.

## Construction

Directed construction passed before source freeze.

- exact UNCHANGED: hash equal and suppressed 3/3;
- SINGLE_PIXEL: equal-hash collision / aHash false suppression 3/3; fallback false suppression0;
- STATUS_DOT_2X2: 3/3 collision; fallback0;
- CURSOR_1X3: 3/3 collision; fallback0;
- GLYPH_STROKE_1X4: 3/3 collision; fallback0;
- LOCAL_BLOCK_4X4: 3/3 collision; fallback0;
- HASH_FLIP positive control: hash changed3/3 and forwarded;
- malformed frame controls rejected5/5.

Mandatory remote readback found only formatting-only source differences before formal: candidate/runner blank-line normalization and removal of an unused audit import. Remote executable bytes were adopted as canonical, local bytes normalized exactly, and the manifest repaired before the formal allocation. Scientific logic, seed, corpus and gates were unchanged.

## Frozen formal

One deterministic formal invocation at seed `155920260918001`; reruns/replacements/tuning `0/0/0`.

| Family | Pairs | aHash equal | aHash false suppress | Exact fallback calls | Fallback false suppress |
|---|---:|---:|---:|---:|---:|
| UNCHANGED | 30,000 | 30,000 | 0 | 30,000 | 0 |
| SINGLE_PIXEL | 30,000 | 30,000 | 30,000 | 30,000 | 0 |
| STATUS_DOT_2X2 | 25,000 | 25,000 | 25,000 | 25,000 | 0 |
| CURSOR_1X3 | 20,000 | 20,000 | 20,000 | 20,000 | 0 |
| GLYPH_STROKE_1X4 | 20,000 | 20,000 | 20,000 | 20,000 | 0 |
| LOCAL_BLOCK_4X4 | 15,000 | 15,000 | 15,000 | 15,000 | 0 |
| HASH_FLIP | 10,000 | 0 | 0 | 0 | 0 |
| **Total** | **150,000** | **140,000** | **110,000** | **140,000** | **0** |

Additional totals:
- MUST_FORWARD changes: 120,000;
- exact-fallback forwarded changes: 120,000/120,000;
- exact unchanged suppressions: 30,000/30,000;
- global aHash false forwards on UNCHANGED:0;
- HASH_FLIP unequal-hash detections:10,000/10,000.

The result is intentionally adversarial, not a natural collision-rate estimate. In this corpus every frozen sparse/tiny family preserves the same global aHash while changing exact state.

## Integrity

Frozen result audit: **PASS**, errors `[]`, copied-result corruption controls7/7 reject.

A separate postformal verifier that imports neither candidate nor runner regenerated the entire 150,000-pair schedule and independently reimplemented the block/global-threshold hash calculation. It reproduced every family metric and total exactly; verifier corruption controls3/3 reject.

- formal result SHA-256: `2649950faa7ca1960632bb9e2eb2dc83d6e43efe5d6d8cdcb1d2ab4275ba4c12`;
- frozen audit SHA-256: `f387f8601a099a806697f5ca0b558f48b10b7492f534340264274c2a9e7cd31a`;
- independent verifier source SHA-256: `dfd48fb2c79de73b6594c2cfc6531b43d78969fdd023e270bcbcc1fb8c038a8f`;
- independent verifier result SHA-256: `eea7b517bc51db4969d3f2784649aefd051589ddba0597b3a80ccd3c70db48f7`;
- deterministic ledger SHA-256: `480325f7b09f3031f5103c1505d148155d7865d222c67bc54f76194f99c1b30f`.

Postformal source rehash is exact against the remote source freeze.

## Interpretation

The scoped negative result supports the existing O1 safety choice: **global perceptual/hash similarity must not be used as suppression authority for tiny local GUI changes**.

An exact fallback restores safety in this corpus, but it executes on all 30,000 unchanged frames plus all 110,000 tiny hash collisions: 140,000/150,000 pairs. That count is a work-path observation only; no latency or performance conclusion is claimed.

The result does not reject:
- task-aware relevant-region gates;
- local hashes tied to explicit ROI/currentness contracts;
- learned relevance models;
- perceptual methods used only as hints or candidate prioritization;
- approximate gates whose uncertainty path is independently proven safe.

## Boundary

Synthetic adversarial gate-safety semantics only. No model accuracy, image-token saving, real-GUI collision rate, task correctness, latency or production-runtime claim. O1 exact comparison and O2 exact tile transport remain unchanged.
