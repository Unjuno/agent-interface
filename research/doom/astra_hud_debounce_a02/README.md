{
  "protocol": "A02: one-frame threshold recurrence / two-frame debounce check",
  "source_commit": "5e5fa2e697109dc68a605bbfcb04e523e3103698",
  "source_csv_sha256": "0b585a3671a10ba2a3e4f634b32cddc7f3fb83aa85013eb75faff8a128cd7e97",
  "rows": 780,
  "threshold_changed_pixels_strictly_greater_than": 60,
  "stable_prefix_source_seconds_lte": 31,
  "stable_prefix_frames": 156,
  "stable_prefix_max_xor": 29,
  "stable_prefix_exceedances": 0,
  "remainder_exceedances": 30,
  "remainder_two_adjacent_exceedances": 0,
  "frame_311_xor": 471,
  "frame_311_has_adjacent_threshold_exceedance": false,
  "remainder_exceedance_frames": [235,274,282,285,302,311,318,326,337,357,360,370,385,402,408,413,426,437,495,506,519,532,535,547,557,571,581,606,618,703],
  "interpretation": "Two-consecutive-frame debounce suppresses every >60-pixel event in this retained trace, including frame 311. Visual-mask temporal resolution only; no event is labeled damage, threat, useful feedback, or safe action trigger."
}
