# A01 plan — pixel-feature screen for retained V39 threat frames

## H/T/D/C/U (fixed before computing image features)

- **H:** In the retained episode's six selected screenshots, a fixed warm-color pixel fraction over the game viewport may differ between the single reviewer-annotated enemy-absent frame (166) and the earliest annotated enemy-present frame (180). A red-pixel fraction may indicate the later visible damage/blood effect (218). These are candidate image features only; no operational guard is proposed.
- **T:** Verify the six PNG SHA-256 values against the prior retained timeline package. Crop the game view at the fixed screenshot coordinates `(322,181)-(960,583)`, then use the upper 80% for scene features to exclude the HUD. Compute: (1) fraction of pixels with `R >= 110`, `R > 1.15*G`, and `G > 1.10*B`; (2) fraction with `R >= 120`, `R > 1.40*G`, and `R > 1.30*B`; (3) consecutive-sample normalized RGB MAE and fraction of pixels whose max-channel absolute difference exceeds 40. No fitting, tuning, or frame exclusion after seeing outputs. Run once; independently recalculate from the retained PNGs.
- **D:** A warm feature screen is positive only if warm fraction at 180 exceeds frame 166 by at least 0.005 (0.5 percentage points). A red-effect screen is positive only if first positive on/after the damage-effect annotated frame 210, and it is interpreted as late evidence. Any result remains exploratory because the input set has one negative frame and no harmless-motion control. If feature thresholds fail, do not propose them for the next test.
- **C:** Camera turn, scenery, weapon, animation, compression/rendering, and lighting can change these color counts. Red can represent non-threat effects; warm colors are common in the scene. One worker supplied the visual labels.
- **U:** Six selected frames from one episode; only frame 166 is labeled enemy-absent, 180–218 enemy-present by one reviewer. No balanced negatives, independent labels, detector calibration, temporal sampling guarantee, false-interrupt estimate, live capture cost, or task-effect evidence. The original episode does not pin its controller commit.

This is an exploratory offline feature screen, not a formal allocation and not a runtime change. Raw screenshots are copied byte-for-byte from `D:\Codex-Research\issue59-current-main-visual-threat-timeline-20261008`; the original timeline record supplies the single-reviewer labels.

## Plan correction before feature computation

Construction check on 2026-10-08 found actual PNG dimensions are 1280x800, not 1280x720. The fixed crop coordinates remain unchanged and are within the screenshot/game window. Update the runner's dimension assertion and reported dimensions to 1280x800; feature definitions, thresholds, frame set, and decision rule remain unchanged. The failed pre-measurement invocation is preserved in `CONSTRUCTION_HOLD_A01.md`.

## Successful-run metadata correction

The first successful feature computation returned the planned numeric results, but the JSON dimension field remained hard-coded to the original incorrect 1280x720 assumption. `RESULT_A01_PRE_METADATA_FIX.json` preserves that first output. The runner was corrected to record the actual verified `rgb.size` (1280x800); no crop, feature, threshold, input, or decision changed. The candidate was rerun to make its saved output reproducible. The independent audit recomputes the features from the six hashed PNGs.
