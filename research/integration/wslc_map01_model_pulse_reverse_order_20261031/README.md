# WSLc MAP01 model pulse contrast: reverse-order pair

This preregistered pair repeats the [prior controlled-pulse study](../wslc_map01_model_pulse_contrast_20261031/) with reversed fixed order: `ae03` 1,000 ms first, `ae04` 500 ms second. Both fresh allocations use the same frozen host, runner, adapter, full X11 image and seed 991031. After guarded navigation, observed held-input cancellation and verified release, fresh review and old-alias refusal, one `gpt-6.1-sol` low-effort call selects action and point. If fire passes the same pixel/binding gates, the experimental duration is applied independently of the model-proposed duration; the prompt discloses this. Eight passive samples follow, with no additional input.

| Pair and allocation | Fixed pulse | Model proposed | Kills before → immediate → final passive sample |
|---|---:|---|---:|
| Prior `ae01` | 500 ms | 500 ms | 0 → 0 → 0 |
| Prior `ae02` | 1,000 ms | 500 ms | 0 → 1 → 1 |
| Reverse `ae03` | 1,000 ms | 1,000 ms | 0 → 0 → 0 |
| Reverse `ae04` | 500 ms | 500 ms | 0 → 0 → 0 |

Both new attempts passed recorded visual and input-stage checks, completed their actions with verified releases, and ended with empty tested keymaps and successful host closures. The 1,000 ms kill observed in the prior pair did not recur in this reverse-order pair. Across these four fixed-seed attempts, the counter increased in 0/2 short and 1/2 long pulses; this is descriptive, not an estimate of general success probabilities or proof of an effect threshold. A zero kill counter in the recorded window does not prove that no shot was emitted or that no later effect occurred. Ammunition change was not sampled.

The attempts have different model calls, inference times and continuing game trajectories; the order was fixed, not randomized, and the four runs are not independent scenarios. Model target selection and timing were not controlled. The simulator supplies the counter, and the cancelled turn may have had a partial effect. These results do not establish task completion, a model-efficiency advantage, or MAP01 completion.

`public.zip` retains both new conditions, frozen code/adapter, screenshots, model output/usage, game samples and guard/owner evidence; private protocol/call files remain local and are hash-indexed in `private-hashes.json`. `python audit.py` with Pillow verifies code identity with the prior pair, hashes, image and coordinate mapping, gates, requested and executed pulse, release ordering and passive samples. WSLc used private Xvfb, network none, one CPU, 1 GiB and a 150 s watchdog.
