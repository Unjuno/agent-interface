# V39 connected-color component screen

This small offline experiment tests one specific visual cue left after the fixed-yellow and global-motion screens: whether grouping warm red/yellow pixels into compact 8-connected components can recover enemy-visible frames without treating diffuse motion as a threat. It uses the existing 36-frame sample and unchanged reviewer labels from merged PR #8472. The labels were fetched and visible before the candidate rule was authored, so this is a posthoc exploratory comparison, not a blinded or preregistered test. It does not relabel the frames or alter their published result.

## H/T/D/C/U

**H — Hypothesis.** Requiring a connected warm-color region of at least 8 pixels in the exact fixed ROI will improve recall over the published yellow-count rule while preserving useful specificity.

**T — Test.** `screen.py` verifies each sampled PNG's byte count and SHA-256, applies the red-or-yellow pixel mask in ROI `[450,250,380,270]`, and marks positive if an 8-connected component has area at least 8. The rule was chosen after the labels had already been fetched and viewed; report it only as posthoc exploratory evidence.

**D — Decision.** A candidate suitable for further trigger testing must improve recall while retaining at least one true negative and avoid positive predictions on all negative controls. The existing yellow baseline is retained as reported, not rerun or edited.

**C — Competing explanation.** Blood particles, projectiles, enemy sprites, and other warm-colored effects share the mask. A connected component may amplify these false positives; one fixed ROI may also miss off-center enemies.

**U — Limits.** This is one retained episode and one reviewer's frame labels, not an enemy detector validation. The source runtime does not pin the controller commit. No game, GUI, model, input, interrupt, release, recovery, task progress, or live allocation was used. It does not establish that any visual cue should interrupt a cover.

## Result

The candidate returns TP=16, FP=18, FN=0, TN=0 (two uncertain labels excluded). The published yellow-count rule on the same sample returned TP=3, FP=0, FN=13, TN=18. Connectedness recovered all labeled positives here but also marked every labeled negative positive; reject it as a cover-switch trigger. This rejects only this frozen color-component rule on this frame sample. It does not reject object-level recognition or scene-conditioned threat assessment.

`CANDIDATE_OUTPUT.json` stores per-frame counts/components and labels; `stdout.txt` and `exit.txt` retain the first command outcome; `AUDIT.json` records an independent recomputation. `FREEZE.json` records the candidate and label-access chronology correction. The main branch baseline and label package came from merged PR #8472. Retained source image inputs are resolved from the local evidence archive listed in `SAMPLE.json` and checked by hash.

Reproduce from this directory with:

```powershell
python screen.py
python audit.py
python -m py_compile screen.py audit.py
python hash_package.py
```

`SAMPLE.json` and `BLIND_LABELS.json` are copied unchanged from merged PR #8472. The source-image resolver uses the repository's `research/doom/results/...` path in a normal checkout; the local workspace fallback points to the preserved audit copy. `ENVIRONMENT.txt` records the local runner and the unavailable WSLc dependency path.

