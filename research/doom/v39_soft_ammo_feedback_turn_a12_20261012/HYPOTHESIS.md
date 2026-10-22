# A12 — soft ammo feedback into the next planner turn

Freeze time: 2026-10-12 before WSLc execution. Source commit is current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`; exact source IDs are in `FREEZE.json`.

**H:** When paired ammo changes from 6 to 4 while remaining above the cover monitor's hard floor of 1, the real monitor should preserve the cover and retain a typed soft event; the real controller summary/helper and `PersistentPlannerAdapter` should include that validated event and current ammo in the next planner input without granting authority. The summary builder should reject a malformed authority claim.

**T:** Build the actual fire cover monitor from a frozen source observation, feed it a same-epoch typed ammo=4 event, pass its event receipt through actual `latest_soft_event_summary` and `begin_model_turn`, and capture the actual adapter's `turn/start` inputs using a recording inert client. Run a malformed soft-event control. Execute once under WSLc with network disabled, one CPU requested, 512 MiB requested.

**D:** PASS_SCOPED requires a non-invalidating soft event, a validated summary containing source/current ammo 6/4 with `grants_input_authority=false`, the same current ammo and summary in the adapter turn input, and rejection of a summary that claims authority.

**C:** Successful prompt delivery does not mean a model noticed, understood, or acted on the feedback. This fixture does not carry a pending live model wait or test whether the cover's duration is appropriate.

**U:** No live model, Doom, GUI/OCR, OS input, key release, feedback utility, recovery bound, ammo consumption, task effect, terminal outcome, or allocation is tested. This verifies feedback delivery only, not end-to-end control.
