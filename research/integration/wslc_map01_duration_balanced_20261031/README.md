# MAP01: model-proposed versus longer firing pulse

Four predeclared WSLc allocations use two seed pairs and a counterbalanced but nonrandom order: 500 ms, 1,000 ms, 1,000 ms, 500 ms. Each uses isolated Xvfb, guarded movement and cancellation, verified release/review, one model-directed 50 ms turn, a fresh second image and model decision, and a gated attack followed by eight passive samples. All second model decisions requested 500 ms; the two 1,000 ms arms intentionally override that value as a predeclared intervention. Simulator labels, angle, ammunition and kills are scorer-only, not model or control inputs.

| Allocation | Seed | Attack | Ammo before / immediately after / final | Kills before / immediately after / final |
| --- | ---: | ---: | --- | --- |
| am01 | 991031 | 500 ms | 50 / 49 / 48 | 0 / 0 / 1 |
| am02 | 991031 | 1,000 ms | 50 / 47 / 47 | 0 / 1 / 1 |
| am03 | 991032 | 1,000 ms | 50 / 47 / 47 | 0 / 1 / 1 |
| am04 | 991032 | 500 ms | 50 / 48 / 48 | 0 / 1 / 1 |

All four recorded a game-reported kill by the final passive sample, verified releases, clear tested keymaps and host closure. In am01, the immediate observation showed zero kills and one round consumed; the first coast sample, about 203 ms later, showed one kill and two rounds consumed. This supports retaining post-release observation rather than treating the first sample as the final task effect. The two longer pulses consumed three rounds and the two shorter pulses consumed two, in these runs.

Four runs on one scenario are too few to estimate general success or infer that duration alone caused any difference. The two model sessions per seed were independent, returned somewhat different target coordinates, used potentially different cache states, and ran at different times. Counterbalancing is not randomization. The earlier canceled input may have had partial effect; release does not undo it. No wait arm is included here; [the prior experiment](../wslc_map01_steer_reobserve_fire_20261031/README.md) supplies only a separate fixed-order wait comparison. A simulator kill and finite key-release observations do not establish MAP01 completion, general safety, or target-tracking reliability.

`public.zip` retains the pre-run hashed runtime snapshot, runner, host, adapter, conditions, screenshots, model output, guards, release records and scorer traces; hashes were checked after execution. `audit.py` (Pillow required) checks both image-response bindings, frozen files, pixel gates, attack durations, release, and counters. The local launcher contains a personal filesystem path and is retained only locally; its pre-run hash is in `private-hashes.json` and each condition. Private model session/call files are likewise excluded but hash-indexed. The hosted model service and host software dependencies were not frozen, and the source snapshot is not asserted identical to the referenced main SHA.
