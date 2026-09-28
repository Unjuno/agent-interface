# Source-schema audit report

The frozen source audit found no event identifier shared across the current v13 physical-release and independent-scorer producers. The release transition schema includes owner/intent data and caller timestamps; the scorer schema includes `event_sequence` and `observed_ns`, with sequence reset in each new `ProgressClock`. Neither producer emits `source_event_id` or a cross-plane scorer epoch key. The disposition is `HOLD_SOURCE_IDENTITY_INSUFFICIENT` for source-identity availability.

This result is static and narrow. It does not establish that live events collided or that no uninspected downstream wrapper adds identity. The retained older v12 per-key measurement has internal `press_id`/`release_id`, but `_edge_for_adapter` omits these IDs; this v12 path is reported separately and is not represented as the active v13 DOWN source.

The synthetic task-effect contract's `source_event_id` test input is not evidence that current producers emit that field. No GPU or container experiment was appropriate for this source-schema question; the requested GPU-backed research remains queued for a separately authorized workload slot.
