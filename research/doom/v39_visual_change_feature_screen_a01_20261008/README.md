# V39 visual-change feature screen A01

This one-run exploratory screen asks whether simple, fixed pixel statistics provide an early cue in six selected frames from the retained `map01-v39-coast-liveness-live-01` episode. The H/T/D/C/U plan is in `PLAN.md`; image bytes and the prior single-reviewer label record are retained under `inputs/`.

## Result

The fixed warm-pixel feature did not distinguish the first annotated threat-present frame from baseline: fraction was 0.000920 at sequence 166 and 0.000565 at sequence 180, a change of -0.000355. The preregistered +0.005 threshold therefore failed. The red-pixel fraction crossed its +0.005 threshold only at sequence 218, where the image has a visible red damage/blood overlay and the existing typed monitor has already hard-invalidated on health below its floor. This is too late to serve as an early threat cue in this trace.

Consecutive-frame whole-scene change was substantial for every selected pair: normalized RGB MAE ranged from 0.0883 to 0.1715, and 15.6%–49.5% of pixels changed by more than 40 in at least one channel. These values include viewpoint, geometry, enemy, and animation changes; with no harmless-motion negative sequence they cannot establish a useful trigger or false-interrupt rate.

**Disposition: REJECT these two fixed color fractions as an early cue for the next live test.** This does not reject general visual threat detection. The sample has one enemy-absent frame and five enemy-present frames from one episode, labels from one reviewer, and no independently labeled harmless-motion controls. Do not add a runtime guard from this screen. A separate, newly authorized matched live comparison remains necessary and must include balanced enemy-present and harmless-motion cases, false interrupts, cancel-to-verified-release, stale-answer rejection, health loss, deaths, and task progress.

## Reproduction and audit

From repository root on Windows with Python 3.11 and Pillow 10.2.0:

```powershell
python research/doom/v39_visual_change_feature_screen_a01_20261008/run_screen.py
python research/doom/v39_visual_change_feature_screen_a01_20261008/audit_screen.py
```

The runner verifies all six source PNG hashes before computing the fixed features. The auditor uses a separate integer-ratio implementation to recompute feature counts and image-transition metrics, checks file hashes, and includes mutation controls for an altered count and altered input hash. `AUDIT.json` records `PASS_INDEPENDENT_RECOUNT` with all five checks true. The initial dimension assertion failure and the corrected output-metadata run are retained in `CONSTRUCTION_HOLD_A01.md`, the correction notes in `PLAN.md`, and `RESULT_A01_PRE_METADATA_FIX.json`.

This is offline construction evidence only. It does not measure detector accuracy, capture or inference latency, live interruption safety, input release, or game outcome. No game, model, GUI, OS input, or new formal/live allocation was used. The current-main V39 visual-threat timeline source is preserved in the copied JSON record; source episode lineage does not pin the original controller commit.
