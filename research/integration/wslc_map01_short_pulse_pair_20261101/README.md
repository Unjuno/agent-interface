# MAP01 200 ms attack pulse versus wait

This WSLc pair changes only the final attack/wait duration of the earlier [991037 seed comparison](../wslc_map01_steer_newseed_pair_20261101/README.md) from 1000 ms to 200 ms, and reverses the arm order. Both arms retain the same fixed navigation, interrupted input and release, review and stale-alias refusal, two full-screen gpt-6.1-sol low calls, model-point patch checks, guarded 50 ms steering and fresh re-observation. The first arm waits 200 ms and the second performs one guarded 200 ms F-key pulse. Both models proposed 500 ms fire; 200 ms is the predeclared experimental pulse, not the model's requested duration. Game labels and counters are evaluator-only.

| Allocation and order | Intervention | Ammo before / after / final | Kills before / after / final | Immediate evaluator labels |
|---|---|---|---|---|
| bb01 first | wait | 50 / 50 / 50 | 0 / 0 / 0 | Zombieman |
| bb02 second | attack | 50 / 49 / 49 | 0 / 0 / 0 | Zombieman, Blood |

Both controls completed, owner and action releases were verified, final tested keys were up and both host sessions closed. The earlier cancelled input retains unknown partial effect. Health stayed 100 in both arms during the recorded window. The simulator's Blood label and ammo decrement are observed signals, not an independent proof of hit or damage; no kill was recorded through eight follow-up samples.

The model calls took 3.254 and 2.246 s in bb01, and 3.709 and 4.195 s in bb02. Input tokens were 26,572 and 26,597, respectively; cached input was 20,224 and 12,032, included in those input totals. Output was 60 and 85 tokens; bb02's reported 23 reasoning-output tokens are a subset of output. Costs are unknown. This is not an end-to-end speed comparison.

The earlier 1000 ms attack used three rounds and recorded no kill; this 200 ms attack used one round and also recorded no kill. Those are separate fixed-order runs with different model wait, provider/cache and possible trajectory effects, not a randomized or matched pulse-duration experiment. Neither result proves that shorter pulses improve accuracy, limit total task cost or solve real-time recovery. The 8x8 patch/geometry gate does not establish semantic target identity, and the model point is not direct crosshair control.

`public.zip` retains the frozen 315-file candidate, conditions, model images/responses and usage, input/release receipts and evaluator samples. Private protocol, call and workspace files remain local and are represented by hashes and sizes; they are not independently audited. Run `audit.py` without Python optimization and with Pillow to check hashes, model-image linkage, stale-alias refusal, guarded steering, the 200 ms pulse and releases, and finite game counters. Host OS, executable and external model service versions are not pinned. This is one seed and one pair; no general combat reliability, live-policy overlap guarantee, MAP01 completion or project completion is claimed. Issues 57 and 59 remain open.
