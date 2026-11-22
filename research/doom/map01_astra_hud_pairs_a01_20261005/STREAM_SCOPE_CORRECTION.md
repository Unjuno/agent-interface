# Retained video scope correction — 2026-10-05

The posthoc stream audit's statement that intermediate image bytes are absent refers to the exact PNGs named by `local-exact-frame-manifest.json` (retained location `results-local/doom/map01-astra-live-01/runtime`). Those 419 per-capture PNG files are not present in this checkout. It does **not** mean that the attempt has no retained visual media: the selected 13 decision-frame PNGs and `research/doom/results/map01-astra-attempt-v1/map01-astra-live-01-2x.mp4` are present.

The adjacent `video.json` records the MP4 SHA-256, 640×560 dimensions, 10 fps, 780 frames, and a 2× playback export of the 149.910820029-second control run. The `STREAM_*` audit did not decode the MP4 or align its frames to monotonic `capture_ns` observations. The MP4 therefore cannot be treated as a byte-exact witness for the missing per-capture PNGs, and this correction makes no claim about health-ROI change or guard latency during model waits.

This note corrects artifact availability wording only. It does not alter `STREAM_FREEZE.json`, the frozen inputs, `STREAM_RESULT.json`, or the prior audit. A future analysis that uses the MP4 would need its own explicit video-to-event synchronization method and additive result; the prospective live threat-exposure gate remains separate.
