# Guarded inline skill cache — H/T/D/C/U

Issue #4260. Additive path only. One semantic operation `ACTIVATE(save)` in a private Xvfb/Tk fixture.

## H
A K=2 guard-bound call-site cache reduces warm full-frame semantic resolution work while preserving exact deoptimization on guard change, unseen shape and old-looking new-generation state.

## T
Policies: `GENERIC_PATH` and `GUARDED_INLINE_CACHE`. Candidate cache entry = current 20x20 marker ROI hash + trusted fixture generation + specialized target coordinate. On miss, candidate executes the exact same full-frame green-target semantic resolver as control and may install/replace one specialization. K=2 LRU.

Frozen ordered phases per fresh arm session: A cold, A warm, B cold, B warm, A warm return, A_MUT same-generation guard change, unseen C, pixel-old-looking A with generation2. Formal: 3 fresh repetitions per policy = 48 operation rows. Construction is excluded. One click per row; application journal independently classifies SAVE_ACTIVATED / wrong effect / miss. No model/provider/network/user desktop.

## D
PASS_GUARDED_INLINE_SKILL_CACHE_SCOPED iff 48 rows reconcile; all application effects are exact SAVE_ACTIVATED and buttons end neutral; A-warm/B-warm/A-return hit in every candidate repetition; A_MUT/C/new-generation A all miss and deopt in every candidate repetition; wrong specialization/effect=0; full-frame generic semantic-scan pixels are strictly lower for candidate; independent audit errors=[]; all frozen corruption controls reject; source unchanged. FAIL on wrong/stale specialization; HOLD if no semantic-work reduction.

## C
Full-frame pixel scan is a deliberately small deterministic generic semantic resolver, not a frontier model. The guard itself has cost. A K=2 cache is fixture-scoped and may thrash on richer shape distributions.

## U
No token/model/general-GUI/product claim. Specialized coordinates are usable only after the current guard+generation match. A cache miss always deoptimizes to current evidence.

## Variables
| field | meaning | SI unit | definition | domain | type |
|---|---|---|---|---|---|
| K | cache capacity | 1 | max live specializations | K=2 | integer scalar |
| generation | trusted surface generation | 1 | fixture manifest value | positive integer | integer scalar |
| guard_hash | current marker ROI digest | 1 | SHA-256 of 20x20 XImage bytes | exact bytes | identifier |
| generic_pixels | pixels inspected by full semantic scan | 1 | one 640x360 scan on generic/deopt | nonnegative | integer scalar |
| guard_pixels | pixels acquired for cache guard | 1 | 20x20 ROI per candidate call | 400 | integer scalar |
| N | formal operation rows | 1 | 2 policies x 3 reps x 8 phases | 48 | integer scalar |

Dimensional check: work endpoints are dimensionless pixel/operation counts; no wall-time threshold is used for PASS/FAIL.
