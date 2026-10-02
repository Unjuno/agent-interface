# Result: physical input occupancy is not identifiable from v39 events

**Disposition:** `PASS_IDENTIFIABILITY_LIMIT` — posthoc telemetry finding only.

The immutable v39 event stream contains 634 rows: 39 per-key input admissions, 28 `keys_held` step snapshots, nine terminal program releases, and one cancellation-time `input_released` event. All nine terminal releases and the cancellation release verify empty keys/buttons. The stream contains **zero per-key release events with a key identity and release timestamp**.

Thus, the trace establishes eventual verified-empty input at program/cancellation boundaries. It does not establish when an individual admitted key physically went up, so actual per-key held-input duration cannot be reconstructed. Program envelope duration, input lease validity, and terminal release time must not be relabeled as key occupancy.

The candidate summary is in `RESULT.json`. `audit.py` independently replays the raw file under a pinned SHA-256 and rechecks the event census/release records. `test_analyze.py` checks four synthetic controls, including a valid per-key release and two incomplete release-shaped records.

No game, model, GUI, input, Docker, GPU, provider, or network action occurred. No original event stream or prior allocation was changed or replayed. This does not satisfy #59's live control gate; it specifies a missing telemetry field for a future separately frozen run.
