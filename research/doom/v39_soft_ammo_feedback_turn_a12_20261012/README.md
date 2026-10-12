# A12 — soft ammo feedback delivery to the next planner turn

This experiment follows A11's positive-ammo boundary into the next-turn feedback path. The frozen V39 `build_cover_monitor` emits a typed soft ammo event when ammo falls from 6 to 4 while remaining above the cover floor of 1. The actual `latest_soft_event_summary` validates and bounds that event, and the actual `begin_model_turn` plus `PersistentPlannerAdapter` place it and the current locally verified ammo into the next turn's text input.

## Result

Both WSLc cases passed. The feedback receipt contains source/current ammo 6/4, the preserved-cover effect, floor 1, and `grants_input_authority=false`; the adapter request contains that exact summary and current ammo 4. A malformed summary claiming it grants authority is rejected. Frozen source identities, raw output, environment, and an independent non-executing audit are included.

This confirms delivery of feedback to a planner request, not that a model understands or uses it. The client only records turn input; no model response is generated. No live game, GUI/OCR, pending-call timing, input, physical release, useful feedback, recovery, task effect, or terminal outcome is established.
