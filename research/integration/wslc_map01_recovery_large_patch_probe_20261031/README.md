# Large-patch matching on retained MAP01 recovery frames

This post-hoc offline probe asks whether a wider pixel template can provide a useful relocation candidate for the two fourth-decision frames rejected in `wslc_map01_crop_recovery_action_20261031`. It reads the saved full source and checked images at the model-selected point. It does not invoke a model, run a game, dispatch input or change a guard. There is no independent object-identity or safe-fire oracle.

The exploratory search compares RGB mean absolute difference on every third pixel of a 48×96 or 80×128 window, over offsets `dx=-96..96`, `dy=-64..64` in steps of two. A distinct runner-up is more than 12 pixels away. As an illustrative post-hoc rule, a match is a `candidate_only` if it is not at the search boundary, its score is at most 32 and its distinct-runner-up margin is at least 4; otherwise it is refused. These thresholds are not calibrated and a candidate grants no input authority. A shifted control is an artificial full-image `(6,-4)` shift; the blank and center-occlusion controls are artificial images, not live scenes.

| Source / case | 8×8 center difference | 48×96 result | 80×128 result |
|---|---:|---|---|
| z01 checked frame | 42.052 | refuse: margin 1.787 | candidate `(0,0)`, score 19.683, margin 8.462 |
| z02 checked frame | 32.083 | refuse: boundary/ambiguity | refuse: boundary/ambiguity |
| z01 synthetic 8×8 occlusion | 149.938 | candidate `(0,0)`, score 2.713 | candidate `(0,0)`, score 0.813 |
| z02 synthetic 8×8 occlusion | 166.667 | candidate `(0,0)`, score 2.929 | candidate `(0,0)`, score 0.861 |

Both window sizes found the expected zero shift for identical images and `(6,-4)` in the synthetic shifted controls; both refused the blank controls. The synthetic occlusion replaces only the model-selected 8×8 point with magenta while leaving the surrounding source image untouched. Both larger windows still produce a high-margin candidate at the original location because the changed pixels are diluted by surrounding pixels. The original center-patch differences detect that constructed change. This demonstrates a concrete failure of using a large-window score and uniqueness margin alone as a safety or target-identity test; it does not establish that either retained live frame was safe or unsafe, nor that any object was actually occluded in the game.

The actual z01 large-window candidate may be dominated by static background; z02's search hits a boundary. The visible game characters and scene changes do not independently prove object identity or action appropriateness. Window sizes, sampling and threshold choices were made after seeing these two failures, so no held-out performance or reliability estimate follows. Wider context might be useful as a **candidate generator** only when combined with separately validated local change, identity, timing, binding and finite-recovery checks. The screenshot-to-input race remains.

`probe.py` recomputes all 20 searches and center-patch controls from the two retained source ZIPs; run it with Python 3.11, NumPy and Pillow. `result.json` retains its output. The source ZIPs were byte-checked against main `ceb1eb2d6bfcf9cf2ee1033956bd6ce6f620600b` (Git blob IDs: z01 `d96d27a535728f84cf618ee0f4d62c6b92da020e`, z02 `93086d0019ebe44518819e2d1394cea81a8566e5`). Local reproducibility was checked with Python 3.11.9, NumPy 2.4.6 and Pillow 10.2.0. This is not a live experiment, model speed comparison or MAP01 completion.
