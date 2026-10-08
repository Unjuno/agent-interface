# Astra continuous HUD excursion A01

This is a retrospective analysis of the retained `map01-astra-live-01` video. It uses no game, model, GUI, or OS-input launch and consumes no live allocation. The question is whether decision-frame sampling hid a transient health change during model inference.

The exact timeline is reconstructed using the same anchor and playback mapping as `research/doom/render_map01_timeline_v1.py`: video frame `i` represents source elapsed time `i / 10 fps * 2x`, anchored to the first observation capture. The retained video has 780 frames and 78 seconds of playback, including its final outcome hold.

At video frame 311 (31.1 seconds playback, source time 62.2 seconds), the rendered overlay shows decision 5, `MODEL THINKING + LOCAL COVER`, and input `cover-5`. The active cover consists of two coast steps and has no input authority. The latest captured observation at that point is sequence 226, 195.335 ms old. This sample falls inside decision 5's model wait and the active `cover-5` interval. Manual review of the retained images reads health as 84% at decision 5, 77% at frame 311, and 84% at decision 6; the selected frame also shows a nearby enemy. Thus two decision samples at 84% conceal at least one intermediate 7-point decrease and recovery while the prior cover was active.

The pixel probe is deliberately narrow. It thresholds red pixels in a fixed HUD rectangle and counts mask changes. Through the decision 4 frame, where the manually read health remains 100%, the largest adjacent mask change is 29 pixels. At frame 311 the mask changes by 471 pixels. The 60-pixel threshold flags this selected visual transition; it does not perform OCR, infer whether health rose or fell, classify threats, or authorize an action. The all-frame measurements are in `samples.csv`.

## Reproduction

From the repository root, with `ffmpeg`, `ffprobe`, Python, NumPy, and Pillow available:

```powershell
python research/doom/astra_continuous_hud_a01/analyze.py
python research/doom/astra_continuous_hud_a01/audit.py
```

`freeze.json` identifies the current-main base and hashes the retained video, metadata, event/report sources, renderer, and all 13 decision frames. `video-frame-311.png` is the exact selected video frame. `audit.json` records source/hash checks, full frame-count and timeline checks, independent ROI recomputation, and the required manual visual spot-checks.

## Interpretation and limits

This demonstrates an intermediate visual state that was absent from the adjacent model-decision samples. It does not identify whether the decrease came from enemy damage, another hazard, or the player's action, or whether the recovery came from a pickup. It does not prove the controller consumed the intermediate observation, that a local policy could safely react, or that any response would improve survival or task completion. The image-derived change signal is not evidence of useful task feedback. A fresh, separately authorized current-main threat-exposure run still needs timestamped observations during model waits, measured release behavior, an independently scored effect, and bounded recovery; the separate live lane remains unassigned.
