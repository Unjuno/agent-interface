# WSLc MAP01 model recovery: crop versus full image

One predeclared sequential pair extends the [single model-directed post-cancellation probe](../wslc_map01_model_after_cancel_20261031/). Both fresh allocations used the same frozen runner and model adapter, Freedoom2 MAP01 skill 1, seed 991031, guarded navigation, an observed held A input followed by cancellation and verified release, fresh review and refusal of the old alias. Each then made one `gpt-6.1-sol` low-effort host call and applied the same center, binding and 8×8 pixel checks before and during a proposed action. The fixed order was crop `ac03`, then full `ac04`. No retrials. The simulator continued advancing during the calls.

| Supplied image | Input tokens | Output tokens | Adapter call time | Model attack | Kill counter at immediate post-action sample |
|---|---:|---:|---:|---|---|
| 640×480 game crop | 11,301 | 52 | 3.755 s | 1,000 ms | 0 → 0 |
| 1280×1024 full screen | 12,476 | 56 | 3.927 s | 500 ms | 0 → 0 |

Both proposed attacks passed the recorded image, binding and three input-stage guards and completed with verified empty releases. The host reported zero cached input tokens for both calls; the input difference is 1,175 tokens (about 9.4% of the full-screen count). Both final tested keymaps were empty and host closures reported success. The observation after each attack was taken immediately; a later game effect was not observed, so a zero counter at that point is not proof that the attack had no eventual effect.

This is one nonrandomized pair, with differing model-selected attack durations and trajectories. It does not establish a general speedup, cost reduction, equal task success, semantic tracking safety, broader recovery reliability or MAP01 completion. The prior single full-screen run recorded a kill; it was not part of this pair. The simulator supplies the game counter, and the cancelled input may have had an unknown partial effect.

`public.zip` retains both conditions, frozen code, screenshots, model responses and provider usage, game samples and guard/owner records. Private model protocol and call artifacts remain local and are indexed only by `private-hashes.json`. `python audit.py` with Pillow rechecks file hashes, exact crop and coordinate mapping, reconstructs the pixel gate, and verifies reported action and release ordering. WSLc used network none, a private Xvfb, 1 CPU, 1 GiB and a 150 s watchdog; the host made the model calls.
