# Retained Astra MAP01 telemetry timeline v1

This posthoc reconstruction adds a decision-interval view of the already
retained `map01-astra-attempt-v1` run. It aligns report and raw-event
monotonic timestamps directly, records the exact held-key events and
observation/admission/release counts, and joins the existing manual HUD
transcriptions by decision index. It does not rerun the game or modify the
historical report, event stream, or original failure diagnosis.

The machine-readable result is
[`timeline-v1.json`](results/map01-astra-attempt-v1/timeline-v1.json). Rebuild
it with `python research/doom/analyze_map01_astra_timeline_v1.py` and verify it
with `python research/doom/audit_map01_astra_timeline_v1.py`. The independent
row audit is mutation-tested by
`python -m unittest research.doom.test_map01_astra_timeline_v1`.

The 13 intervals account for 528 of the 530 raw observations; two initial
observations precede the first model-start boundary. They include all 46
per-key `input_admission` events and all 26 terminal records whose release
receipt says `verified: true`; these counts are not program-admission counts.
Eight contingencies were authored and none were taken. Decision-frame HUD values
show health falling from 100 to 0 and ammo from 50 to 37, with the ammo loss
concentrated in decisions 3–4. The controller later issued turn/forward
repositioning commands while health declined from 84 to 0, but the retained
telemetry does not establish route progress, enemy identity, or why damage
occurred. Model assessments are not independent threat annotations, and
viewport effect receipts only report pixel change. These associations cannot
attribute damage to any individual input or cover policy.

The retained 2x video remains useful for qualitative visual review, but this
timeline deliberately relies on raw event telemetry and exact decision-frame
HUD transcription instead of treating the encoded video as a frame-exact
observation stream. The result is diagnostic evidence for the failed retained
attempt, not a corrected threat-exposure run, a successful recovery, or a
MAP01 completion claim.
