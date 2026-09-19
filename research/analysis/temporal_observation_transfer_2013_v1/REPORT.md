# Temporal observation transfer fixture (#2013)

## Result

**PASS_TEMPORAL_OBSERVATION_TRANSFER_FIXTURE_SCOPED**

The controlled live-like fixture records four timestamped observations at t=0, 10, 20, and 40. The t=30 interval is intentionally absent and is reported as a dropped/missing interval, never as an invented unchanged frame.

The role query selects the latest observation at or before the current time for `current`, and selects the first observation at or after the action anchor (19) for `after_action`. These resolve to distinct, provenance-bearing records (t=40 and t=20 respectively). The exact ROI (x=1..3, y=1..2) reconstructs identically from the historical record.

Controls passed:
- source/session/surface provenance present;
- missing interval remains absent;
- current vs historical role confusion rejected;
- non-monotonic timestamp ordering rejected;
- wrong-surface scope rejected.

Observed output digest: `a5e68c6e721491bf84e476dbc5ea6b96c571e87877d834ab6b19d41e47abd48c`.
Formal checks: 1; independent audit: 1; reruns: 0; tuning: 0.

## Boundary

This is a deterministic, controlled live-like fixture, not a GUI/X11 capture, production runtime, model inference, network interaction, or human-tempo result. It establishes the transfer semantics and evidence bookkeeping only. No claim is made about real-world capture cadence or downstream UI behavior.
