# V39 soft-event carry across a hard-invalidated planner turn (A05)

## H / T / D / C / U

**H:** If a soft typed event is observed while a V39 planner turn is pending and a later hard event invalidates/cancels that turn, V39 retains the soft event on the canceled decision record. The next iteration can serialize it into the next prompt; cancellation delays this context but does not discard it.

**T:** On current main `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`, inspect the exact V39 `main` AST path. Confirm the invalidation branch appends `cover_validity_soft_events` and `cover_validity_latest_soft_event` before `continue`; confirm the next loop derives `latest_soft_event_summary(decisions)` before `begin_model_turn`; execute the exact summary and prompt-builder helpers on a synthetic canceled-decision record carrying a prior ammo soft event. The planner is a stub.

**D:** PASS the scoped carry hypothesis only if source order confirms the decision record is appended before the continue, includes the event count and latest event, and the exact helper serializes that event into the subsequent stub prompt without granting authority.

**C:** Source-composition probe with one synthetic decision record. No model, game, GUI, OS input, container, or live allocation.

**U:** This does not demonstrate an actual in-flight planner interruption, a live image/OCR observation, whether the event changes model behavior, independently useful feedback, cover switch, key release, recovery, task progress, or MAP01 outcome. It only identifies the current control-flow route following a canceled turn. The #59 live threat-exposure gate remains open.

## Result

The bounded source check passed: in the `invalidation is not None` branch, V39 appends the canceled decision including both soft-event fields and then continues. The next loop's `latest_soft_event_summary(decisions)` consumes that record before building the next planner prompt. An exact-helper stub run preserved the prior ammo event and `grants_input_authority=false`. Thus soft feedback is delayed until the canceled turn resolves, then remains available to the following turn. See `RESULT.json`, `audit_successor_A02.json`, preserved audit-v1 failure under `audit_v1/`, and `COMMANDS.txt`.
