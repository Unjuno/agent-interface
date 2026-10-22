# Retained MAP01 video health timeline (post-hoc A01)

## H / T / D / C / U

- **H:** the retained 2x MAP01 video contains health HUD changes between its 13 exact decision screenshots; localizing them may distinguish cover-period damage from a post-response pickup that decision-only values hide.
- **T:** `python -B research/doom/results/map01-astra-video-health-timeline-v1/run_timeline_v2.py` decodes the pinned 780-frame video, applies the specified red-mask rule to one 95x50 health ROI, records each threshold transition, aligns it with report model-call intervals, and saves crops. `python -B .../audit_timeline.py` independently re-decodes the source, rechecks transitions and crop hashes.
- **D:** the expected 30 transition frames must match exactly; crops and source video hashes must validate; endpoint must be 100% to 0%; a +24-point recovery must be visible.
- **C:** video is 10 fps at 2x playback, so event onset is bounded to 0.2 source seconds. The crop contains the red health digits and percent icon. Numeric values are manual transcriptions from preserved after-transition crops; the event detector identifies pixel changes, not the number. Model-window classification uses `ready.emit_ns` as zero and recorded model timestamps.
- **U:** one exploratory post-hoc clip analysis only. RUN01 preserved an aggregation failure; RUN02 is the corrected offline analysis. HUD values are not a game-state sensor; pixel changes do not establish semantic usefulness, causal damage attribution, control efficacy, matched speed, or MAP01 success. The package adds no live input, game, model, or allocation evidence. This is exploratory post-hoc analysis, not preregistered or confirmatory evidence; the transition threshold and manual transcription were selected after initial viewing.

## Result

Thirty health changes were visible between the strategic decision screenshots. The timeline shows health falling from 100 to 60 during model-call windows, rising 24 points from 60 to 84 between calls, then falling to 0. Summed digit changes indicate 100 gross health points lost during coast-cover inference, 13 during the single active-hold inference window, and 11 while no model call was pending; the +24-point pickup is separate. These are HUD-delta associations in one clip, not causal damage attribution. The decision-only summary's 84-point sum of negative coast-window end-to-end changes therefore hides both intermediate damage and recovery.

The extracted transition crops are in `transition-crops/`; three review sheets are provided. The source video is the immutable `map01-astra-attempt-v1` recording with SHA-256 recorded in `TIMELINE.json`.
