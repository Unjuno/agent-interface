# WSLc MAP01: scripted watched and unmonitored controls

Four predeclared independent episodes use a fixed fixture policy: fire at (636,526) for 500 ms, with a 2 s fixture pending window. No model was called. Seeds 991037 and 991038 each have one watched and one unmonitored run, ordered watch/baseline then baseline/watch. The same candidate, seed within each pair, target and action were used; separate episodes and wall-clock game evolution are not perfectly matched. The snapshot is not asserted identical to main.

| Seed | Watch | Action result | Ammo | Hits | Damage | Neutral release |
|---|---|---|---|---|---|---|
| 991037 | yes | cancelled; partial effect unknown | 50 to 49 | 1 | 15 | verified |
| 991037 | no | completed | 50 to 48 | 1 | 15 | verified |
| 991038 | no | completed | 50 to 48 | 1 | 15 | verified |
| 991038 | yes | cancelled; partial effect unknown | 50 to 49 | 1 | 15 | verified |

In both watched cases a natural target-patch difference exceeded the threshold during the held key. The cancellation was acknowledged, but independent owner release is the evidence of neutral input. This shows the watch can interrupt the intended fixed action in these two episodes; it does not establish that the change was safe or unsafe, identify what caused it, measure a false-positive rate, establish general reliability, or complete MAP01. The experiment is not an end-to-end model benchmark. More seeds, matched timing and independently labeled environmental events remain needed.

`public.zip` preserves all four raw receipts, fixture messages, screenshots, frozen sources, conditions and hashes of local private command files. SHA-256: `eb06c8ed5514dcff56b0f88a5993b36754c14ffa401600b569752688fd5215af`. Run `python audit.py` without `-O` (Pillow required) to recompute patch differences, validate guards, cancellation/release ordering, input state and counters. Host and container exited for every run; WSLc listed no active allocation afterwards.
