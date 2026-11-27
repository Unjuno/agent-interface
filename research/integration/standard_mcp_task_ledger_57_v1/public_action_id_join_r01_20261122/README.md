# Public action ID join R01

Status: `PASS_SYNTHETIC_IDENTITY_JOIN`. Current main `f5c87f4bef26be604bb6872e63ee2274d1c9bbd3` used `action_call_id` both as the recorder's `tool_call.call_id` and the public `interface_dispatch` body's server-generated `call_id`. Those are different identity domains: recorder IDs are assigned at the caller boundary, while the runtime creates its own public action ID. The adapter therefore could not join a normally recorded live response unless the caller fabricated equality.

## Change

The research adapters now resolve exactly one `interface_dispatch` event by parsing its retained public response and matching the response body's `call_id` to the action ID in the score / owner receipt. Recorder tool-call IDs remain the IDs for journaling, exact result lookup, ordering, and raw-response custody. Operation ID and target generation continue to be cross-checked across dispatch, exact result lookup and owner receipt. Ambiguous dispatches fail closed.

Tests include a completed-action capture/effect receipt where recorder ID `d…d` differs from public action ID `a…a`, and the recorded-caller Relay recovery path where recorder ID `f…f` differs from public action ID `a…a`.

## Verification

Five focused comparison/effect/owner suites passed **68/68 normally and 68/68 under `-O`** on CPython 3.11.9 / Windows 10 build 26300. Full outputs are `combined-normal.log` and `combined-optimized.log`. The 33-test focused effect + recorder suites also passed normally and under `-O`.

This packet has no GUI dispatch. It repairs the offline identity join needed to ingest a future fresh live caller run; it does not retrofit R06, establish public `task_success`, or establish efficiency or recovery reliability. The next gate is a fresh current-main run with the recorder instrumented at call boundaries, then a separate recovery trial.

Initial test-authoring attempts exposed two test fixture defects (the synthetic IDs were still equal; then the recorder receipt was referenced before creation). They did not reveal a runtime regression; after correcting the fixture, the final retained suites passed. Details are in `excluded-attempts.md`.
