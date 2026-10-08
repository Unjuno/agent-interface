# Astra decision-4 dense HUD replay A01 (#59)

## H / T / D / C / U

**H.** The retained 2x video samples health at 10 encoded frames/s (0.2 game-seconds/frame) and can narrow when the first health loss occurred during decision 4's 11.741-second model call. It may also distinguish damage observed before the model returned from damage that falls across the return boundary.

**T.** Replay the exact 640x560, 10-fps, 78-second retained video over playback seconds 22.3–28.2 (game clock 44.6–56.4), extracting all 60 frames of the health HUD ROI. Compare each crop's RGB pixels with the first in-wait sample. Independently recompute the first changed frame with a separate thresholded-pixel count. Preserve selected full-frame stills at the wait start, last unchanged sample before the first health change, first changed sample, final waiting frame, first post-wait frame, and end of the primary action.

**D.** PASS_DESCRIPTIVE only if the 44.6-second frame shows decision 4 `MODEL THINKING + LOCAL COVER`, the health ROI matches the 100% baseline through game time 46.8, its first pixel-state transition appears at 47.0, the last frame labelled waiting at 56.2 reads 94%, and the first frame labelled local plan at 56.4 reads 87%. Report the source frame cadence and phase boundary resolution; do not assign the 94→87 loss to the wait alone.

**C.** This is a posthoc read of one edited 2x video and one failed allocation. The recorded stream is 10 fps at 2x playback (one frame per 0.2 game seconds); a transition is bounded by adjacent samples. HUD values and overlay labels are manually transcribed from retained stills; RGB template-distance output is corroboration, not OCR. Video compression, manual reading, and overlay sampling can obscure sub-frame ordering.

**U.** This does not establish why damage occurred, semantic threat detection quality, policy appropriateness, a causal effect of the local cover, an operational guard, current V39 behavior, useful task feedback, recovery efficacy, latency bounds, or MAP01 success. No game, model, GUI, or OS input was run. The private live-game lane remains unassigned and this replay does not allocate it.

## Pilot and frozen analysis

Before freezing this package, a read-only visual pilot inspected the retained video at selected timestamps and suggested a health transition during decision 4's wait. The package labels that provenance as exploratory. The frozen A01 analysis then covers every encoded frame in the selected six-second interval, preserves selected stills, and independently recomputes the pixel-change boundary. It is descriptive posthoc evidence, not a preregistered live experiment.

## A01 outcome

The frozen pixel replay finds no health-ROI change from game time 44.6 through 46.8, then a changed health glyph at 47.0. The adjacent samples bound the first recorded visible loss to `(46.8, 47.0]` game seconds, about 2.4 seconds after the first frame labelled as model-thinking with local cover. The manually transcribed HUD reads 100% at 46.8 and 96% at 47.0.

The last sampled frame labelled model-thinking/local-cover is at 56.2 seconds and reads 94% health / 37 ammo. At 56.4 seconds, the overlay has moved to local plan/feedback and the HUD reads 87% / 37. The 94→87 loss therefore crosses the observed model-return boundary and cannot be assigned solely to model wait. The model eventually returned a backward + turn-right plan. These observations sharpen the old 100→84 decision window without claiming causal damage timing.

At 44.6 seconds, the cover-4 frame reads 46 ammo; by 53.8 seconds it reads 37 while the model is still pending. The selected waiting frame at 56.2 also reads 37. These selected frames show a nine-round net decrease after the first sampled waiting frame; they do not identify when each shot occurred or why firing stopped. The retained report's broader 48→37 window includes activity before the first sampled pending frame.

See `FREEZE.json`, `CONTAINER_EXECUTION.txt`, `RESULT.json`, `results/a01/candidate.raw.json`, `results/a01/independent_audit.json`, and `results/a01/samples/`. Recompute the candidate and audit only against the frozen input; do not rerun the underlying game allocation.

The candidate and auditor refuse to overwrite an existing output and use exclusive file creation. To recompute, set `RESULT_DIR` to a fresh directory; the candidate writes `candidate.raw.json` there and the auditor writes `independent_audit.json` without replacing either retained A01 artifact.
