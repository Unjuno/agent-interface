# Astra decision-4 wait video review A01

## H / T / D / C / U

- **H:** During the retained 11.741-second decision-4 wait, the primary Doom game view may show an apparent enemy while `cover-4` is still active. The edited video's exact frame-to-controller-observation mapping is not retained.
- **T:** Decode every frame from playback 22.3–28.2 seconds (game 44.6–56.4 seconds), 0.1 playback seconds / 0.2 game seconds apart, from the frozen video blob. Review all 60 full frames and retain RGB hashes, contact sheets and selected stills.
- **D:** Record `OBSERVED_MAIN_VIEW_ONLY` when an apparent enemy is visible in the single first-person game scene during the pending `cover-4` interval. Do not claim the controller consumed the exact video frame without a byte/sequence join.
- **C:** The clip is posthoc and labelled; its capture/composition pipeline is undocumented. Apparent sprite identity and exact runtime timing can be misread.
- **U:** This does not establish the precise controller observation at game time 50.4 s, threat onset, policy appropriateness, response efficacy, damage causality, recovery or task effect.

## Corrected result

The first manual pass called the top portion of frame 252 a “secondary panel” and called the weapon's lower foreground a separate primary viewport. That was a visual interpretation error. Rechecking the full-resolution frame shows one continuous 640×480 Doom first-person scene. The upper portion is the distant room/opening; the lower portion is the foreground floor, weapon and HUD. There is no visible panel boundary. The separate controller input screenshot retained for decision 4 likewise contains a single 640×480 game window inside a 1280×800 desktop capture.

Across the 60 hash-pinned frames, at game time 50.4 seconds (frame 252), the overlay still says `MODEL THINKING + LOCAL COVER` and `input: cover-4`; an apparent enemy sprite is visible at the right side of the primary game scene. The HUD reads 96 health and 41 ammo. At 56.2 seconds the last sampled pending frame shows 94 health and 37 ammo, without a clear enemy. At 56.4 seconds the overlay changes to local plan/feedback and health reads 87.

Disposition: **OBSERVED_MAIN_VIEW_ONLY; CONTROLLER_FRAME_JOIN_UNPROVEN**. The repository event log records `cover-4` observation captures during the wait (sequences 194–204), but those raw image bytes are not retained here for a pixel-identity join to video frame 252. The video therefore supports an apparent threat in the primary game view during the pending-cover period, but not proof that V39 or any controller received that exact view. This is Astra retrospective evidence, not the fresh current-main V39 threat-exposure test required by Issue #59.

The correction is recorded separately in `VISUAL_CORRECTION_A01.json`; the original freeze, initial manual review, raw output and source/frame audit remain unchanged for provenance. The original audit checks source bytes, decoded frame identity and selected stills; it does not verify the semantic interpretation.

No live game, model, GUI, OS input, Docker/container, or allocation was used. The private live-game lane remains unassigned.

## Reproduction

From the repository root, with PyAV 18.1.0 and Pillow installed:

```powershell
python research/doom/results/map01-astra-wait-secondary-panel-a01-20261005/audit.py
```

The retained `run_review.py` is the original one-shot decoder; do not run it again because it intentionally refuses to overwrite `raw.json`. The audit reopens the frozen Git blob and independently checks source hash, all 60 decoded RGB hashes/timestamps, and five selected still identities. It does not adjudicate visual labels or verify controller frame consumption.
