# V39 dual soft-signal coalescing boundary (A04)

H: When both health (100→96) and ammo (46→37) change within their current soft-validity envelopes in one advancing typed observation, V39 records both transitions but its single `latest_soft_event` slot sends only one typed signal to the following planner turn.

T: Execute the current V39 `DoomCoverSignalPairMonitor` with the frozen production observable guard against one synthetic sequence-2 pair carrying health 96 and ammo 37. Then execute the exact `latest_soft_event_summary` helper on the resulting two-event count and final event. Sources are current-main lineage at `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`; neither model, game, input, nor GUI is started.

D: PASS boundary finding if monitor returns no invalidation, counts two soft changes, retains only ammo as the latest event (guard iteration order health then ammo), and the summary preserves count 2 plus ammo values while containing no health event. Otherwise retain the exact result as counterevidence.

C: Synthetic construction probe of event coalescing and next-turn serialization only. The chosen values are inside configured guard envelopes; no OCR, model use, tactical appropriateness, release, recovery, task progress, or live outcome is measured.

U: The result establishes an information-loss boundary in the current typed-event handoff. It does not show that the omitted health change would change a model decision or improve task outcome. No live allocation is assigned or implied.

Observed result: monitor accepted the pair, `soft_event_count=2`, retained signal `ammo` at 37; the actual summary reports both occurred (`soft_event_count=2`) but serializes only ammo (46→37). Health 100→96 is absent from next-turn context. This is consistent with the explicit newest-event-only contract; it is a design limitation, not an unannounced runtime failure.
