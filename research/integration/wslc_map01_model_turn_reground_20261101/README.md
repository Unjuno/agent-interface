# WSLc MAP01: model-guided turn and re-ground after cancellation

The first preregistered attempt dp01 stopped before turning because `aim-turn` violated the session alias grammar. The owner cleanup verified neutral input. This failed attempt is retained; successor allocations use a corrected alias. These trials use a candidate snapshot, not a claim that the entire runtime equals main.

In each successor, a model-selected fire was interrupted by natural or injected patch change, with partial effect unknown and separate verified input release. Following explicit read-only review, a third `gpt-6.1-sol` call selected an off-center target. After image/binding checks, one 100 ms right turn completed with verified release. A fourth call then received a new frame; a fresh patch and binding gate controlled whether another 200 ms shot could run. Four model calls were requested at low effort per episode.

- dq01: the sampled angle changed 103.71 to 98.44 degrees; the fourth target fell within the configured center gate. The guarded recovery fire completed and release was verified. Ammo fell 49 to 48, but hits stayed 1 and damage stayed 15: a shot was observed, **not an additional hit**.
- dq02: the angle changed 100.20 to 93.16 degrees. The fourth target was within the center gate, but its patch difference was 44.06, above 32, so the recovery shot was refused. Final cleanup verified neutral input.

The turn is uncalibrated and uses independent episodes. These data do not establish reliable aim, a semantic threat response, general recovery or MAP01 completion. The first fire's unknown partial effect is never replayed. A bounded turn plus fresh model grounding can lead to a new independently released action, while changing observations can still prevent it.

`public.zip` preserves the failed and successor candidates, conditions, model results and usage, images, receipts and private-file hashes. SHA-256: `afe46067bb53be6b3b683c09649889c3c9cabaf672b77969a4638b9cb1235366`. Run `python audit.py` without `-O` (Pillow required) for integrity, model provenance, review, turn/release, post-turn image gate, shot counters and refusal. All hosts and containers exited; WSLc listed no active allocations.
