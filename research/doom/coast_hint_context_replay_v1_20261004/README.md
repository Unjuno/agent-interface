# Bounded typed-health context replay (v39)

This package tests whether early typed observations that are discarded by the unauthored-coast monitor can be retained as bounded *historical prompt context* after exact reconciliation to a later full observation. It replays the one retained v39 coast-liveness episode; it does not modify or execute the live controller.

## Frozen inputs and run

The report, raw event stream, and v2 retained audit are copied unchanged from the v39 outcome. The replay binds their SHA-256 values in `coast-hint-exact-stream-replay.json`. Run from the repository root:

```powershell
python research/doom/coast_hint_context_replay_v1_20261004/replay.py
python -m unittest discover -s research/doom/coast_hint_context_replay_v1_20261004 -v
python research/doom/coast_hint_context_replay_v1_20261004/audit.py
```

The replay feeds only typed/full observation rows emitted during unauthored-coast model waits into `coast_hint_candidate.py`. A typed row is retained only after later exact full-observation reconciliation on id, step, sequence, capture time, pointer binding, and RGB hash. At each recorded model turn, context is bound to that decision's exact `source_image` observation and excludes samples at or after its sequence. Authored-policy waits are not modified.

## Result

Six decisions replay. The candidate retains and exactly reconciles 26 and 20 and 21 typed rows in unauthored waits 0, 2, and 3. It would add historical context to turns 1, 3, and 4 where the recorded baseline soft-event summary is empty: respectively three health-97 samples, health 76/73, and three health-68 samples. The JSON reports the exact sequences, timestamps, ammo values, and context sizes. The stable d0 wait adds only repeated 97 readings; the d2 wait's latest three history at d3 includes the decline to 76/73.

The independent audit checks input and candidate hashes, the retained formal audit flag, event counts, exact identity joins, prior unauthored-wait provenance, no-authority/no-success flags, and unchanged recorded final-admission labels.

## Limits

This is a deterministic replay of one selected trajectory, not a prospective or randomized test. Presence in a prompt does not show that a model would use the history correctly or improve task effects. No mid-turn interrupt, policy invalidation, action, token saving, safety, or game completion is simulated. The live allocation is consumed and was not rerun. This package supports considering a prospective no-interrupt context test only; it does not justify production integration or efficacy claims.
