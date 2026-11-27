# Offline replay: larger masked templates on live candidate-oracle frames

This post-hoc exploration reuses two recorded WSLc episodes from `wslc_map01_shadow_candidate_oracle_20261101/public.zip` (SHA-256 `84f5e89a84ac4135043c50558eff5b493234c13ce2fff2312cbfa3272b5bb04f`). No new game, model or input is run. In each episode, the original model target is inside the enemy label on a paired simulator/model screen. The later checked X11 crop matches the evaluator game screen outside the synthetic 8×8 overlay, and evaluator labels are used only for scoring.

A candidate translation is searched on a ±80×±60-pixel grid at two-pixel spacing. For every candidate, the central 8×8 pixels of its square template are excluded from the RGB absolute-difference sum. The minimum is selected without using the enemy label. This moving central mask is a sensitivity experiment, not a verified occlusion detector. The template sizes and this approach were chosen after seeing the retained frames.

| Episode | 16×16 candidate | 32×32 candidate | 48×48 candidate |
|---|---|---|---|
| ec01 | `(718,478)`, outside | `(640,554)`, inside | `(732,570)`, outside |
| ec02 | `(727,495)`, outside | `(735,491)`, outside | `(701,599)`, outside |

One of six candidates lies inside the corresponding sampled enemy rectangle. Larger patches and central masking alone therefore do not consistently preserve the target in these examples. Rectangles are simulator-only labels, not proof of semantic identity, and there are only two scenes with a synthetic perturbation; these observations do not estimate a general failure rate, benchmark live latency, justify dispatching a candidate, or establish MAP01 completion. The existing production safeguards are unchanged.

Run `python audit.py` without `-O` (Pillow and NumPy required) to verify the pinned archive and member hashes, source/checked screen alignment, labels, and all 4,941 masked scores per size. The original experiment record is not modified.
