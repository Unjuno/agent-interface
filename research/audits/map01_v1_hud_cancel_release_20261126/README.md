# MAP01 displayed HUD decrease and cancellation of a held key

One registered Freedoom MAP01 trial on 2026-11-26 JST met the screen-triggered cancellation and release criterion. The controller read 100% on the health display, then 97% while Up was held, and sent one cancellation. The X11 input owner verified that the key had been released. A separate view of the same display read 100% again in the next frame. [Machine-readable summary](SUMMARY.json)

## Trial and observations

The trial used source `79b8d36aa026475a8b0c09b195fa8343ac787fa9`, the unmodified `map01-threat-contact-v1` save, skill 1 and seed 26011261. The registered program allowed one forward Up hold of at most 4.5 seconds. The game ran on a private X11 display in a dedicated WSL2 control group, with a 75-second episode limit. The program issued no firing command or damage injection. Provider and model calls both totaled zero.

Before task input, two pairs of neutral one-tic refreshes checked that the post-load game clock was advancing. The immediate pair advanced one tic and the pair separated by a wait advanced 71. The controller then captured 11 images. Its first ten health readings were 100%, and sequence 11 read 97%. An independent passive capture recorded 22 frames. Enlarged glyphs from frames 16, 17 and 18 read 100%, 97% and 100%. Ammunition read 50 throughout both streams.

## Input release and retirement

The executor accepted one program and admitted one Up key. The cancellation matched that program. The owner's X11 keymap showed keycode 111 down before release and up afterward. It verified all keys and buttons neutral and published the release before the cancelled program terminal. On this trial the controller frame capture preceded verified neutral by 53.977102 ms, including 3.507007 ms from the runtime cancel request to verified neutral.

The game, input owner, window manager and Xvfb process identities retired. The passive witness joined, the service control group disappeared and the display lock was absent. The runner and service both exited with status zero.

## Independent audit and limits

The offline audit recomputed all 2,376 file digests in the private raw manifest and both digests in the separate HUD review manifest. It checked the controller and passive image digests, the release and terminal records, and the 40 independent V15 scorer samples. The registration and manifest SHA-256 values are in the summary. The underlying images and host records remain private.

V15 recorded no death, kill or map exit during the sampled interval. Its samples contain no engine health value. The cause of the displayed decrease, the return to 100% and the source of any attack remain unknown. The timing describes this one cancellation. The earlier stationary trial used a different fixture and input, so the two trials do not isolate the effect of movement. [Earlier trials and clock diagnostic](../map01_formal_holds_clock_20261126/README.md)
