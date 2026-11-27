# WSLc MAP01: threshold 150, natural and injected controls

Four preregistered independent episodes use the same fixture fire action, target (636,526), two seeds and bounded pending window as the earlier scripted threshold-32 experiments. The monitor threshold alone is changed from 32 to 150; the pre-dispatch image guard remains 32. Each seed has one natural episode and one artificial magenta-overlay positive control, ordered natural/inject then inject/natural. No model is called. The source snapshot is not claimed to equal main.

| Seed | Condition | Maximum sampled difference | Outcome | Ammo | Hits / damage |
|---|---|---:|---|---|---|
| 991037 | natural | 120.146 | held action completed | 50 to 48 | 1 / 15 |
| 991037 | injected | 164.250 | cancellation requested | 50 to 49 | 1 / 15 |
| 991038 | injected | 164.995 | cancellation requested | 50 to 49 | 1 / 15 |
| 991038 | natural | 124.505 | held action completed | 50 to 48 | 1 / 15 |

Independent neutral release was verified in all four runs. Interrupted actions have unknown partial effect. At threshold 150 these natural trials were not interrupted and the strong synthetic controls were detected. That does not establish whether the natural change was safe, nor whether the high threshold would miss a consequential smaller change; no false-negative or false-positive rate, general safety, optimal threshold, model performance, or MAP01 completion follows. Separate episodes and timing are not perfectly matched. More realistic independently labeled environmental changes and replicated conditions are needed before any production policy change.

`public.zip` includes frozen source, preregistered conditions, fixture messages, screenshots, raw observations and action/release receipts. SHA-256: `49a31bdd7e91a35aab462b39a05a134a3524865c0f19a9a8179c8327f2166d7b`. Run `python audit.py` without `-O` (Pillow required) to recompute image differences and check guards, fixture, cancellation, releases and counters. All hosts and containers exited and WSLc listed no remaining allocations.
