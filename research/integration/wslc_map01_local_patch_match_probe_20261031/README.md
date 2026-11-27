# Local patch matching on retained MAP01 model observations

This post-hoc, offline probe asks whether a moving target rejected by the 8x8 stale-pixel gate in #9907 and #9908 can safely be re-anchored by nearest pixel match rather than another model call. It reads exactly the saved model source image and checked fresh observation from ee02.zip and ff01.zip; both ZIPs were verified byte-for-byte against main 3b04714a3eb13caea5bdb1a1b51002b520e2658d. There is no new game, GUI, model, input, or allocation. A square search examines all integer offsets within ±48 pixels using RGB mean absolute difference; 8x8, 16x16 and 24x24 patches are compared. A second candidate must be more than 8 pixels from the best. The illustrative post-hoc gate refuses a boundary match, margin under 4, or best score over 32. These choices are exploratory and do not authorize input or establish semantic identity.

| Saved pair | Patch | Best offset | Best score | Distinct second margin | Exploratory decision |
| --- | ---: | --- | ---: | ---: | --- |
| ee02 | 8 | (-6, +48) | 7.56 | 1.62 | refuse: boundary, ambiguous |
| ee02 | 16 | (-5, +48) | 9.46 | 1.08 | refuse: boundary, ambiguous |
| ee02 | 24 | (+46, -40) | 13.41 | 2.65 | refuse: ambiguous |
| ff01 | 8 | (-6, +48) | 22.25 | 6.54 | refuse: boundary |
| ff01 | 16 | (+35, +14) | 25.60 | 0.02 | refuse: ambiguous |
| ff01 | 24 | (+35, +16) | 23.72 | 0.90 | refuse: ambiguous |

The lowest pixel error alone would select a location even when the checked ff01 image no longer shows the previously visible central hostile. That visual inspection is not a ground-truth object-tracking oracle, and the best match is not proved to be any particular object. The boundary/ambiguity rule rejects these two cases, but it also rejects ee02's identical-image and known-shift controls because their next distinct match is too similar. For ff01 the identical-image and synthetic (+5,-3) shift controls return the expected offset and pass this illustrative gate; a blank image is rejected for both sources. Thus the rule is conservative and can refuse a correct match; neither those controls nor two selected pairs qualify it as a general tracker.

`probe.py` checks the saved source image and fresh artifact SHA-256, recomputes the complete search and prints deterministic JSON; `result.json` retains the first output. Python 3.11.9, NumPy 2.4.6 and Pillow were used locally. The search and thresholds were chosen after inspecting the failures, so these are not held-out performance estimates. A semantic target, subsequent change, X11 check-to-press race, game effect, and safety remain unresolved. This probe does not replace a model, dispatch a key, change runtime code, or establish MAP01 completion.
