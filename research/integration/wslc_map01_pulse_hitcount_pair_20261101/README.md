# MAP01 200 ms pulse: evaluator hit and damage counters

This fresh WSLc pair extends the [200 ms attack/wait control](../wslc_map01_short_pulse_pair_20261101/README.md). The candidate retains the same fixed route, seed 991037, model-directed steering, fresh re-observation and guarded 200 ms final action, but adds ViZDoom `HITCOUNT`, `DAMAGECOUNT`, `HITS_TAKEN` and `DAMAGE_TAKEN` to evaluator samples. These counters are not passed to the model or control gates. The official [ViZDoom game-variable documentation](https://vizdoom.farama.org/1.2.4/api/python/enums/) describes HITCOUNT as hits on monsters/players/bots and DAMAGECOUNT as damage dealt; they are simulator counters, not an independent physical oracle.

| Allocation and order | Final action | Ammo before / after / final | Hits before / after / final | Damage before / after / final | Kills before / after / final |
|---|---|---|---|---|---|
| cc01 first | guarded 200 ms attack | 50 / 49 / 49 | 0 / 1 / 1 | 0 / 15 / 15 | 0 / 0 / 0 |
| cc02 second | 200 ms wait | 50 / 50 / 50 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

Both recorded zero hits taken and damage taken at these checkpoints, neutral action and owner releases, empty final tested keys and successful host closure. The game labels include Blood immediately after cc01; the counter increment and visual marker come from the same simulator and are not independent confirmations. The earlier cancelled turn retains an unknown partial effect. The attack and wait runs are separate episodes with independent model decisions and nonidentical timing; this pair supports a scoped game-reported effect but not an isolated causal or reliability estimate. Neither run recorded a kill during eight follow-up samples.

The model's two proposals requested 500 ms fire in each arm, while 200 ms was fixed by the experiment. Model call times were 5.299 and 2.795 s for cc01, 3.915 and 2.250 s for cc02. Each arm used 26,579 input and 60 output tokens; cached input was 12,032 and 0 respectively and is included in input. Cost is unknown. These are not end-to-end speed or cost comparisons.

`public.zip` retains frozen candidate bytes and hashes, model images/responses/usage, action and release receipts, evaluator samples and conditions. Private protocol and call/workspace files remain local and are represented only by hashes and sizes, not independently audited. Run `audit.py` without Python optimization and with Pillow to verify source and image hashes, cancellation/review/stale-alias ordering, guarded 200 ms pulse or wait, releases, exact raw sample linkage and counters. WSLc used private Xvfb, network none, one CPU / 1 GiB, pinned image and 180 s watchdog; host OS, executable and model service versions are not pinned.

One fixed seed and one pair, a development-selected route, a non-semantic 8x8 patch guard and fixed pulse do not establish target identity, broad real-time control reliability, autonomous policy overlap or MAP01 completion. Issue 57 and Issue 59 remain open.
