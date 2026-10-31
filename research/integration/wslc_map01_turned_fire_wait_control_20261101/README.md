# WSLc MAP01: bounded turn followed by fire/wait controls

Four preregistered scripted episodes use two seeds, ordered fire/wait then wait/fire. After an initial fire is interrupted by a natural patch change, its effect remains unknown; input release and a read-only window review precede the same fixed 100 ms right turn in both arms. That turn completes with independently verified release. The recovery phase then fires for 200 ms or waits for 200 ms. The evaluator saves a simulator state screen and label rectangles before the phase, without giving them to the action policy. No model is called; the snapshot is not asserted identical to main.

| Seed | Recovery | Enemy box `(x,y,w,h)` before | Ammo | Hits | Damage | Kills |
|---|---|---|---|---|---|---|
| 991037 | fire | `(320,226,41,67)` | 49 → 48 | 1 → 2 | 15 → 30 | 0 → 1 |
| 991037 | wait | `(310,228,28,59)` | 49 → 49 | 1 → 1 | 15 → 15 | 0 → 0 |
| 991038 | wait | `(320,226,41,69)` | 49 → 49 | 1 → 1 | 15 → 15 | 0 → 0 |
| 991038 | fire | `(322,227,28,59)` | 49 → 48 | 1 → 1 | 15 → 15 | 0 → 0 |

The nominal screen center is `(320,240)`. It lies at the left edge of the first fire box and outside the second fire box at the recorded sample. A hit and kill occurred during one fire interval, not the other or the waits. These separate episodes differ in target size, placement and time, so the comparison does not establish a general hit probability or prove attribution of the earlier model-guided dt01 kill. The fire phases took about 345–352 ms including setup and release; waits took about 200 ms, so this is not a speed comparison. No MAP01 completion or general recovery reliability is established.

`public.zip` preserves frozen candidate, conditions, fixture messages, same-state evaluator screens and labels, turns, action/release receipts and counter samples. SHA-256: `9311494da6f3c192af1b4a5a46c9858a87979b8b95ea194adc92bc09d0333019`. Run `python audit.py` without `-O` (Pillow required) to check manifests, review, turns, fire versus wait, screen hashes, labels, counters and neutral input. All hosts and containers exited and WSLc listed no active allocation.
