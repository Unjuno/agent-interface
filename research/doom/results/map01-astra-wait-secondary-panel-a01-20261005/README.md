# Astra decision-4 secondary-panel review A01

## H / T / D / C / U

- **H:** During the retained 11.741-second decision-4 wait, the labelled video may show an apparent enemy in a secondary panel while the primary player viewport points at a wall. Whether that panel is part of any controller-consumed screenshot is unknown.
- **T:** Decode every frame from playback 22.3–28.2 seconds (game 44.6–56.4 seconds), 0.1 playback seconds / 0.2 game seconds apart, from the frozen video blob. Review all 60 full frames, preserve their RGB hashes, contact sheets, and selected full-resolution stills.
- **D:** Record `OBSERVED_PANEL_ONLY` if a clear apparent enemy is visible in the secondary panel during the model-pending `cover-4` interval while the primary viewport lacks that enemy; do not treat this as controller-visible evidence without source provenance.
- **C:** The panel may be an editorial or contextual view. A threat shown to a video viewer is not necessarily shown to the runtime. Manual labels can also be mistaken.
- **U:** This is posthoc visual evidence from one edited video. It does not establish panel origin, runtime observation access, enemy onset, policy appropriateness, controller response, or any causal/task outcome.

## Result

All 60 frames were decoded from the hash-pinned 640×560, 10 fps video. At game time 50.4 seconds (frame 252), while the overlay still says `MODEL THINKING + LOCAL COVER` and `input: cover-4`, the upper/secondary panel visibly contains an apparent Doom enemy sprite. The lower primary viewport shows the weapon facing a wall; its HUD reads 96 health and 41 ammo. At 56.2 seconds, the last sampled pending frame shows 94 health and 37 ammo, with no clear enemy in either visible scene panel. At 56.4 seconds the overlay changes to local plan/feedback and health reads 87.

The finding is deliberately classified **OBSERVED_PANEL_ONLY**. The video sidecar gives codec, dimensions, FPS, duration, and source hash, but does not describe the extra panel or bind it to the controller's captured client surface. The apparent enemy therefore cannot be used as evidence that V39 could have detected or reacted to it. The separate decision-4 input frame at the start of the wait and live model/runtime path remain distinct evidence.

This narrows what the existing video can support and motivates capturing the exact controller-consumed frame stream in any future authorized threat exposure. The private live-game lane remains unassigned; no live allocation was invoked.

## Reproduction

From the repository root, with PyAV 18.1.0 and Pillow installed:

```powershell
python research/doom/results/map01-astra-wait-secondary-panel-a01-20261005/run_review.py
python research/doom/results/map01-astra-wait-secondary-panel-a01-20261005/audit.py
```

The audit reopens the frozen Git blob and independently checks the source hash, complete frame count/timestamps, every decoded RGB hash, and the retained selected stills. It does not validate manual semantic labels or infer that the secondary panel was available to the controller.
