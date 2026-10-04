# Astra video health transitions joined to raw input events

This posthoc analysis joins the 30 red-HUD transitions in the retained 2x video
timeline from PR #7434 to the original monotonic event stream. The video time
origin (`ready.emit_ns`) is verified against all 13 report model-call windows;
every start and end matches exactly at the timeline's recorded precision.

Five health-transition windows contain a per-key `input_admission` event.
Eight overlap a `keys_held` acknowledgement to its matching `step_completed`
event envelope. Those eight include seven health decreases and one 24-point
increase. This is temporal coincidence only. The envelope is not an exact
physical key-up interval, and overlap does not establish damage cause or input
effectiveness. The remaining video timing is bounded by its 10 fps, 2x export.

Rebuild the join with
`python research/doom/join_map01_astra_health_events_v1.py`, audit the saved
result with `python research/doom/audit_map01_astra_health_events_v1.py`, and
run five mutation tests with
`python -m unittest research.doom.test_map01_astra_health_events_v1`.
The machine-readable output is
[`EVENT_INPUT_JOIN_V1.json`](results/map01-astra-video-health-timeline-v1/EVENT_INPUT_JOIN_V1.json).

This analysis uses the same failed Astra run and does not fulfill the live
threat-exposure, useful-response, bounded-recovery, or MAP01 completion gates.
