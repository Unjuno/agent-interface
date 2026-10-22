# Retained video localization of the Astra ammo decrease

## H / T / D / C / U

- **H:** The manually observed 48→37 HUD decrease between exact observations 148 and 211 can be localized in the retained 2x video and compared with the concurrent local-cover input lifecycle.
- **T:** Decode the hash-pinned 640×560, 10 fps MP4 with PyAV; map video PTS to monotonic source seconds using its recorded 2× playback factor; manually read the ammo HUD before/after each pixel transition; join each 0.2-second bracket to `cover-4` key acknowledgements, step completions, plan-3 owner release, and decision-4 model start/end. An independent auditor re-decodes the source, verifies crops/hashes, and recomputes event joins.
- **D:** `PASS_POSTHOC_VIDEO_TEMPORAL_ASSOCIATION_HOLD_CAUSAL_ATTRIBUTION` records that the three selected observation endpoints align within 100 ms, the manually read 11 one-round HUD decrements are bound to decoded before/after crops, and every transition bracket overlaps a `cover-4` lifecycle envelope whose acknowledged key set includes `space`. The independent audit checks source/crop hashes and timing joins; ammo numerals remain manual. Causality remains HOLD.
- **C:** The ammunition decreases are temporally consistent with repeated local-cover fire holds while decision 4 is being inferred. Delayed game consumption, video/event-clock mapping error below the 0.2-second sampling bound, or another unobserved source could still contribute. A `keys_held`-to-`step_completed` envelope is not a physical key-state measurement.
- **U:** Single failed trajectory, manual HUD transcription, lossy 10 fps 2x export, 0.2-second source-time transition bounds, no game ammo telemetry or physical key-up samples, and no counterfactual. No live allocation or input was run.

## Result

The video source-time mapping is checked at three retained event observations: sequence 117 at 35.180776 s maps to frame 176 at 35.2 s (manual ammo 50); sequence 148 at 43.975750 s maps to frame 220 at 44.0 s (48); and sequence 211 at 57.066684 s maps to frame 285 at 57.0 s (37). The video contains 11 one-round decrements in brackets from 44.2–44.4 s through 53.6–53.8 s.

| Video-bounded source interval (s) | Manual HUD change | Overlapping `cover-4` step |
|---|---:|---:|
| 44.2–44.4 | 48→47 | 0 |
| 44.4–44.6 | 47→46 | 0 |
| 44.8–45.0 | 46→45 | 0 |
| 46.6–46.8 | 45→44 | 2 |
| 47.0–47.2 | 44→43 | 2 |
| 48.8–49.0 | 43→42 | 4 |
| 49.2–49.4 | 42→41 | 4 |
| 51.0–51.2 | 41→40 | 6 |
| 51.4–51.6 | 40→39 | 6 |
| 53.4–53.6 | 39→38 | 8 |
| 53.6–53.8 | 38→37 | 8 |

All 11 brackets overlap one of five `cover-4` `keys_held`-to-`step_completed` intervals with `space` in the key set (steps 0, 2, 4, 6, and 8; each also holds `a` or `d`). Plan 3's owner-side empty release was verified at source time 44.073109 s, before the first decrement bracket. Decision 4's model window is 44.476180–56.320775 s: one decrement precedes its start, one bracket straddles the start, and nine are wholly inside. This makes repeated local-cover firing a concrete temporal explanation for the ammo loss and weakens the earlier inference that the non-firing planner command alone left an unexplained 11-round drop. It does not prove that a particular input caused the game to consume each round.

## Reproduction

```powershell
python research/doom/map01_astra_hud_pairs_a01_20261005/ammo_video_timeline.py
python research/doom/map01_astra_hud_pairs_a01_20261005/audit_ammo_video_timeline.py
python -m unittest discover -s research/doom/map01_astra_hud_pairs_a01_20261005 -p test_ammo_video_timeline.py -v
```

Manual frame/value annotations and the extraction ROI are pinned in `AMMO_VIDEO_ANNOTATIONS.json`. The decoded transition and endpoint HUD crops are retained under `ammo-video-transition-crops/` and bound by `AMMO_VIDEO_RESULT.json` and `SHA256SUMS`. The previous endpoint-only ammo analysis remains as historical scope; this additive timeline does not change its source inputs or claim.
