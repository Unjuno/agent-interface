# A03 — does the delayed soft event reach the following planner prompt?

## H / T / D / C / U (frozen before candidate execution)

**H:** Once V39 has finished a planner turn and recorded the A01 ammo `SOFT_CHANGED` event (46→37), the actual `latest_soft_event_summary` and `begin_model_turn` helpers serialize that event into the following planner prompt, preserving the source/current values, sequence, hard floor, and no-authority semantics.

**T:** On current main `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`, extract the exact `latest_soft_event_summary` and `begin_model_turn` functions from the V39 controller. Feed the unchanged A01 result event as the most recent completed decision to the summary helper, then call the actual prompt builder with a stub planner and current locally verified ammo 37. No model is called.

**D:** PASS_NEXT_TURN_DELIVERY iff the actual summary helper accepts the A01 event, returns ammo source 46/current 37 with its original sequence and minimum, and the actual prompt builder passes the exact serialized summary to the planner stub in one `begin_turn` call. Otherwise retain the exact failure; no retry.

**C:** This tests one synthetic event and a stub planner call only. A01/A02 establish that the event was first received during a previous pending model turn and persisted after that turn returned; this A03 tests only its next-prompt representation.

**U:** Delivery on a later turn does not show that the planner uses the signal well, that the signal arrives before damage or a bad action, that the event can cancel/switch a current cover, or any real OCR, input release, recovery, task progress, survival, or MAP01 outcome. No live-game allocation is assigned or implied.
