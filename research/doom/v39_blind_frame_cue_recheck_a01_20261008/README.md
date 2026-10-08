# V39 blind-frame recheck of the fixed yellow cue (A01)

## Question and limits

Does the previously reported fixed yellow-pixel rule fire on a reproducible random sample of retained V39 frames that an independent reviewer labels without sequence numbers or cue values?

This is a secondary, post-hoc, single-episode screen. The sample selection and cue rule were fixed before visual labeling, but the cue itself was proposed after the source episode. One reviewer labeled frames; labels are not an independent ground truth. No controller, game, model, input backend, or live allocation was run.

## H/T/D/C/U

- **H:** The existing yellow cue (`R>180, G>100, B<100, R>0.8G, G>1.5B`, count `>200` in ROI `[450,250,830,520]`) may identify visible enemies in the retained `map01-v39-coast-liveness-live-01` screenshots.
- **T:** From the 217 manifest-listed numeric PNG frames (sequence 151 is missing), select 36 without replacement using Python `random.Random(5908)`. Shuffle opaque labels with the same RNG. Before unblinding sequence numbers and cue counts, label each image `present`, `absent`, or `uncertain` for an enemy visibly present in the scene. Then calculate the frozen cue on the same ROI.
- **D:** Preserve every frame label and pixel count. Exclude uncertain labels from the 2x2 table. This sample is descriptive; it has no promotion threshold and cannot validate a detector.
- **C:** The frame selection can miss rare false positives. The reviewer may confuse distant sprites, corpses, effects, or occlusion; one episode is not an independent sample of encounters.
- **U:** No blind second reviewer, attack-source labels, benign-motion matched episode, temporal tracking, false-interrupt rate under a live controller, cancel/release latency, causal task effect, or recovery evidence is established.

## Result

The blind labels were 16 enemy-visible, 18 enemy-not-visible, and 2 uncertain. After unblinding, the yellow cue fired on 3/16 clearly enemy-visible frames and 0/18 clearly enemy-absent frames: TP=3, FN=13, FP=0, TN=18. Thus observed recall is 18.75%; the zero false positives in this small sample does not contradict the known sequence-30 player-muzzle-flash false positive in the full episode, because sequence 30 was not selected.

The result supports only a low-recall warning for this fixed cue on this episode. Do not use it as an autonomous interrupt predicate. It does not rule out other visual features or establish that an earlier interrupt would improve play.

## Provenance and reproduction

- Sample source commit: `dd9c2cde511a52cf21e80ecbb2eb9edb0dd6f2f8`.
- Publication/current-main source checked: `1aaa633c4f1aeec25e4b4617d92dd93af3b20603`.
- Retention manifest: `research/doom/results/map01-v39-coast-liveness-live-01/retention-manifest.json`.
- All 36 sampled frame byte counts and SHA-256 values match both the frozen sample record and the current-main retention manifest.
- `SAMPLE.json` records the seed, opaque labels, source frame IDs, sizes, and hashes. `BLIND_LABELS.json` records the labels before the sequence mapping is joined. `OUTPUT_PREVIOUS.json` records the original local calculation.
- Reproduce pixel counts with `python3 reproduce.py`; independently recheck selection, source hashes, counts, and confusion table with `python3 audit.py`. Both require ImageMagick `magick` on `PATH`.

This evidence is additive and does not satisfy Issue #59's fresh live threat-exposure gate.
