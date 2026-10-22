# A13: soft-ammo feedback to fresh action admission

Hypothesis: when a soft ammo event is delivered through the real persistent planner adapter into a new model-turn input, the current-main fresh action admission helper rejects a fire candidate whose planner-authored minimum ammo exceeds the current ammo. A matching-ammo positive control should reach the helper's executor-ready status without executor admission or input authority.

Classification: construction-only integration evidence. The event, adapter and admission helper are real current-main software paths. Candidate output is synthetic; no model is invoked. No executor, game session, live allocation, physical input, or live-control outcome is tested.

Frozen base: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
