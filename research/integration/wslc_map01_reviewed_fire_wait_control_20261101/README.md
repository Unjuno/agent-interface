# WSLc MAP01: reviewed recovery fire versus wait

Four preregistered scripted episodes use two seeds, ordered fire/wait then wait/fire. After a first fire is interrupted by a natural patch change, its effect remains unknown; the action releases input and the focused window is explicitly reviewed. The recovery phase then either fires for 200 ms with a separately verified release or waits for 200 ms without dispatch. No model is called. The evaluator records screen and labels from one ViZDoom state immediately before the phase and samples counters afterwards; these evaluator data do not drive the actions. The candidate snapshot is not asserted identical to main.

| Seed | Recovery | Ammo before → after | Hits | Damage | Kills |
|---|---|---|---|---|---|
| 991037 | fire | 49 → 48 | 1 → 1 | 15 → 15 | 0 → 0 |
| 991037 | wait | 49 → 49 | 1 → 1 | 15 → 15 | 0 → 0 |
| 991038 | wait | 49 → 49 | 1 → 1 | 15 → 15 | 0 → 0 |
| 991038 | fire | 49 → 48 | 1 → 1 | 15 → 15 | 0 → 0 |

The sampled enemy rectangle was right of nominal screen center in all four cases; the scenes were not identical. These controls show ammunition use on fire but no added hit or kill in either arm. They do not explain or attribute the kill in the earlier model-guided dt01 episode, where aim, timing and scenario differed. The 200 ms input hold is not a matched end-to-end phase duration: fire phases took about 349–351 ms including setup and release, while wait phases took about 200 ms. This is neither a speed comparison nor MAP01 completion.

`public.zip` preserves frozen candidate, conditions, fixture messages, same-state evaluator screenshots and label rectangles, action/release receipts and counter samples. SHA-256: `6f6bd4f0581230293423fc820f74b314a5e322230bec7cea645a44a0a77b4375`. Run `python audit.py` without `-O` (Pillow required) to check manifests, prior release and review, action versus wait, screenshot hash, label positions, counters and terminal neutral input. All hosts and containers exited and WSLc listed no active allocation.
